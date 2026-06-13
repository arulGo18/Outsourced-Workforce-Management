from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import models, schemas, database
import random
from datetime import datetime
from fastapi import UploadFile, File
import shutil
import os
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import re
import cv2
import numpy as np

from fastapi import (
    UploadFile,
    File
)

router = APIRouter()

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# =========================
# DATABASE DEPENDENCY
# =========================
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================
# CREATE WORKER
# =========================
@router.post("/create-worker")
def create_worker(data: schemas.CreateWorker, db: Session = Depends(get_db)):

    worker = models.Worker(
        nama=data.nama,
        nik=data.nik,
        no_kk=data.no_kk,
        jenis_kelamin=data.jenis_kelamin,
        alamat=data.alamat,
        email=data.email,
        no_hp=data.no_hp,
        vendor=data.vendor,
        posisi=data.departemen,
        tipe_kontrak=data.tipe_kontrak,
        nama_rekening=data.nama_rekening,
        no_rekening=data.no_rekening,
        bank=data.bank
    )

    # 1. simpan worker
    db.add(worker)
    db.commit()
    db.refresh(worker)

    # 2. generate ID
    new_id = "ID" + str(random.randint(1000, 9999))

    # 3. simpan ke worker_ids
    worker_id = models.WorkerID(
        worker_id=worker.id,
        id_pekerja=new_id,
        status="inactive"
    )

    db.add(worker_id)
    db.commit()

    # 4. activity log
    activity = models.Activity(
        worker_id=worker.id,
        activity_type="CREATE",
        status="SUCCESS",
        description=f"Worker dibuat dengan {new_id}"
    )

    db.add(activity)
    db.commit()

    return {
        "message": "Worker berhasil dibuat",
        "id_pekerja": new_id
    }


# =========================
# GET WORKER BY ID
# =========================
@router.get("/worker/{id_pekerja}")
def get_worker_by_id(id_pekerja: str, db: Session = Depends(get_db)):

    worker_id = db.query(
        models.WorkerID
    ).filter(
        models.WorkerID.id_pekerja
        == id_pekerja
    ).first()

    worker_id_data = db.query(models.WorkerID).filter(
        models.WorkerID.id_pekerja == id_pekerja
    ).first()

    if not worker_id_data:
        return {"message": "ID tidak ditemukan"}

    worker = db.query(models.Worker).filter(
        models.Worker.id == worker_id_data.worker_id
    ).first()

    # ambil placement aktif
    placement = db.query(models.WorkerPlacement).filter(
        models.WorkerPlacement.worker_id == worker.id,
        models.WorkerPlacement.end_date == None
    ).first()

    # 🔥 ambil nama lokasi (INI YANG TADI ERROR)
    placement_data = None
    if placement:
        placement_data = db.query(models.Placement).filter(
            models.Placement.id == placement.placement_id
        ).first()

    return {
        "nama": worker.nama,
        "nik": worker.nik,
        "agency": worker.vendor,
        "dept": worker.posisi,
        "kontrak": worker.tipe_kontrak,
        "status": worker_id.status,
        "lokasi": placement_data.nama_penempatan if placement_data else None
    }


# =========================
# AKTIVASI WORKER
# =========================
@router.post("/activate-worker")
def activate_worker(

    data: schemas.ActivateWorker,

    db: Session = Depends(get_db)
):

    # =========================
    # CARI WORKER ID
    # =========================
    worker_id_data = db.query(

        models.WorkerID

    ).filter(

        models.WorkerID.id_pekerja
        == data.id_pekerja

    ).first()


    # =========================
    # JIKA ID TIDAK ADA
    # =========================
    if not worker_id_data:

        return {
            "message":
            "ID tidak ditemukan"
        }


    # =========================
    # CEK DISABLED WORKER
    # =========================
    disabled_worker = db.query(

        models.DisabledWorker

    ).filter(

        models.DisabledWorker.id_pekerja
        == worker_id_data.id_pekerja

    ).first()


    # =========================
    # JIKA DINONAKTIFKAN ADMIN
    # =========================
    if disabled_worker:

        activity = models.Activity(

            worker_id=
            worker_id_data.worker_id,

            activity_type=
            "ACTIVATE",

            status=
            "INVALID",

            description=
            "Gagal aktivasi karena ID dinonaktifkan admin"
        )

        db.add(activity)

        db.commit()

        return {

            "message":
            "ID telah dinonaktifkan oleh admin dan tidak dapat diaktifkan kembali"
        }


    # =========================
    # JIKA SUDAH AKTIF
    # =========================
    if worker_id_data.status == "active":

        activity = models.Activity(

            worker_id=
            worker_id_data.worker_id,

            activity_type=
            "ACTIVATE",

            status=
            "INVALID",

            description=
            "Gagal aktivasi karena ID sudah aktif"
        )

        db.add(activity)

        db.commit()

        return {

            "message":
            "ID sudah aktif, lakukan penempatan di menu Mutasi"
        }


    # =========================
    # UPDATE STATUS
    # =========================
    worker_id_data.status = "active"

    db.commit()


    # =========================
    # SIMPAN PENEMPATAN
    # =========================
    placement = models.WorkerPlacement(

        worker_id=
        worker_id_data.worker_id,

        placement_id=
        data.placement_id,

        start_date=
        datetime.now(),

        end_date=None
    )

    db.add(placement)

    db.commit()


    # =========================
    # LOG AKTIVITAS
    # =========================
    activity = models.Activity(

        worker_id=
        worker_id_data.worker_id,

        activity_type=
        "ACTIVATE",

        status=
        "SUCCESS",

        description=
        f"Aktivasi ke placement ID {data.placement_id}"
    )

    db.add(activity)

    db.commit()


    return {

        "success": True,

        "message":
        "Worker berhasil diaktivasi"
    }


# =========================
# MUTASI WORKER
# =========================
@router.post("/mutasi-worker")
def mutasi_worker(data: schemas.MutasiWorker, db: Session = Depends(get_db)):

    worker_id_data = db.query(models.WorkerID).filter(
        models.WorkerID.id_pekerja == data.id_pekerja
    ).first()

    if not worker_id_data:
        return {"message": "ID tidak ditemukan"}
    
    # CEK DISABLED WORKER
    disabled_worker = db.query(

        models.DisabledWorker

    ).filter(

        models.DisabledWorker.id_pekerja
        == worker_id_data.id_pekerja

    ).first()


    # =========================
    # JIKA DINONAKTIFKAN ADMIN
    # =========================
    if disabled_worker:

        activity = models.Activity(

            worker_id=
            worker_id_data.worker_id,

            activity_type=
            "MUTATION",

            status=
            "INVALID",

            description=
            "Gagal mutasi karena ID dinonaktifkan admin"
        )

        db.add(activity)

        db.commit()

        return {

            "message":
            "ID telah dinonaktifkan oleh admin dan tidak dapat dimutasi kembali"
        }

    # tutup placement lama
    last_placement = db.query(models.WorkerPlacement).filter(
        models.WorkerPlacement.worker_id == worker_id_data.worker_id,
        models.WorkerPlacement.end_date == None
    ).first()


    # cek apakah lokasi sama
    if last_placement and last_placement.placement_id == data.placement_id:

        activity = models.Activity(
            worker_id=worker_id_data.worker_id,
            activity_type="MUTATION",
            status="INVALID",
            description="Gagal mutasi karena lokasi sama"
        )

        db.add(activity)
        db.commit()

        return {
            "message": "Worker sudah berada di lokasi tersebut, pindahkan ke loakasi lain"
        }

    if last_placement:
        last_placement.end_date = datetime.now()
        db.commit()

    # tambah placement baru
    new_placement = models.WorkerPlacement(
        worker_id=worker_id_data.worker_id,
        placement_id=data.placement_id,
        start_date=datetime.now(),
        end_date=None
    )

    db.add(new_placement)
    db.commit()

    activity = models.Activity(
        worker_id=worker_id_data.worker_id,
        activity_type="MUTATION",
        status="SUCCESS",
        description=f"Mutasi ke placement ID {data.placement_id}"
    )
    db.add(activity)
    db.commit()

    return {
        "message": "Mutasi berhasil"
    }

# =========================
# EDIT CONTRACT
# =========================
@router.post("/edit-contract")
def edit_contract(data: schemas.EditContract, db: Session = Depends(get_db)):

    # cari worker id
    worker_id_data = db.query(models.WorkerID).filter(
        models.WorkerID.id_pekerja == data.id_pekerja
    ).first()

    if not worker_id_data:
        return {"message": "ID tidak ditemukan"}
    
    # =========================
    # CEK DISABLED WORKER
    # =========================
    disabled_worker = db.query(

        models.DisabledWorker

    ).filter(

        models.DisabledWorker.id_pekerja
        == worker_id_data.id_pekerja

    ).first()


    # =========================
    # JIKA DINONAKTIFKAN ADMIN
    # =========================
    if disabled_worker:

        activity = models.Activity(

            worker_id=
            worker_id_data.worker_id,

            activity_type=
            "EDIT_CONTRACT",

            status=
            "INVALID",

            description=
            "Gagal edit kontrak karena ID dinonaktifkan admin"
        )

        db.add(activity)

        db.commit()

        return {

            "message":
            "ID telah dinonaktifkan oleh admin dan tidak dapat mengubah tipe kontrak"
        }

    # cari worker
    worker = db.query(models.Worker).filter(
        models.Worker.id == worker_id_data.worker_id
    ).first()

    if not worker:
        return {"message": "Worker tidak ditemukan"}
    

    if (
        worker.tipe_kontrak == data.tipe_kontrak
        and
        worker.posisi == data.departemen
    ):
        
        activity = models.Activity(
            worker_id=worker.id,
            activity_type="EDIT_CONTRACT",
            status="INVALID",
            description="Gagal edit kontrak karena data sama"
        )

        db.add(activity)
        db.commit()

        return {
            "message": "Tidak ada perubahan data, lakukan perpindahan kontrak dengan data yang sudah di validasi."
        }
    

    # update data
    worker.tipe_kontrak = data.tipe_kontrak
    worker.posisi = data.departemen

    db.commit()

    # activity log
    activity = models.Activity(
        worker_id=worker.id,
        activity_type="EDIT_CONTRACT",
        status="SUCCESS",
        description=f"Kontrak diubah menjadi {data.tipe_kontrak}"
    )

    db.add(activity)
    db.commit()

    return {
        "message": "Kontrak berhasil diperbarui"
    }



@router.get("/activities")
def get_activities(vendor: str, db: Session = Depends(get_db)):

    activities = db.query(models.Activity).order_by(models.Activity.created_at.desc()).all()

    result = []

    for act in activities:

        worker = db.query(models.Worker).filter(
            models.Worker.id == act.worker_id
        ).first()

        if worker and worker.vendor != vendor:
                continue

        result.append({
            "tanggal": act.created_at.strftime("%d-%m-%Y %H:%M"),
            "nama": worker.nama if worker else "-",
            "nik": worker.nik if worker else "-",
            "vendor": worker.vendor if worker else "-",
            "activity": act.activity_type,
            "status": act.status,
            "description": act.description
        })

    return result

# =========================
# GET ALL WORKERS
# =========================
@router.get("/workers")
def get_workers(vendor: str, db: Session = Depends(get_db)):

    workers = db.query(models.Worker).filter(
        models.Worker.vendor == vendor
    ).all()

    result = []

    for worker in workers:

        # ambil worker id
        worker_id = db.query(models.WorkerID).filter(
            models.WorkerID.worker_id == worker.id
        ).first()

        # ambil placement aktif
        placement = db.query(models.WorkerPlacement).filter(
            models.WorkerPlacement.worker_id == worker.id,
            models.WorkerPlacement.end_date == None
        ).first()

        lokasi = "-"

        if placement:
            placement_data = db.query(models.Placement).filter(
                models.Placement.id == placement.placement_id
            ).first()

            if placement_data:
                lokasi = placement_data.nama_penempatan

        result.append({
            "id_pekerja": worker_id.id_pekerja if worker_id else "-",
            "nama": worker.nama,
            "vendor": worker.vendor,
            "lokasi": lokasi,
            "departemen": worker.posisi,
            "status": worker_id.status if worker_id else "-",
            "tipe_kontrak": worker.tipe_kontrak
        })

    return result

# =========================
# GET WORKER DETAIL
# =========================
@router.get("/worker-detail/{id_pekerja}")

def get_worker_detail(
    id_pekerja: str,
    vendor: str,
    db: Session = Depends(get_db)
    ):

    worker_id = db.query(models.WorkerID).filter(
        models.WorkerID.id_pekerja == id_pekerja
    ).first()

    if not worker_id:
        return {"message": "Worker tidak ditemukan"}

    worker = db.query(models.Worker).filter(
        models.Worker.id == worker_id.worker_id
    ).first()

    if worker.vendor != vendor:
        return {
             "message": "Akses ditolak"
        }

    placement = db.query(models.WorkerPlacement).filter(
        models.WorkerPlacement.worker_id == worker.id,
        models.WorkerPlacement.end_date == None
    ).first()

    lokasi = "-"

    if placement:
        placement_data = db.query(models.Placement).filter(
            models.Placement.id == placement.placement_id
        ).first()

        if placement_data:
            lokasi = placement_data.nama_penempatan

    return {
        "id_pekerja": worker_id.id_pekerja,
        "status": worker_id.status,

        "nama": worker.nama,
        "nik": worker.nik,
        "no_kk": worker.no_kk,
        "jenis_kelamin": worker.jenis_kelamin,
        "alamat": worker.alamat,
        "email": worker.email,
        "no_hp": worker.no_hp,

        "vendor": worker.vendor,
        "departemen": worker.posisi,
        "tipe_kontrak": worker.tipe_kontrak,

        "nama_rekening": worker.nama_rekening,
        "no_rekening": worker.no_rekening,
        "bank": worker.bank,

        "lokasi": lokasi
    }

# =========================
# CREATE WORKER PLAN
# =========================
@router.post("/create-worker-plan")
def create_worker_plan(
    data: schemas.CreateWorkerPlan,
    db: Session = Depends(get_db)
):

    plan = models.WorkerPlan(

        tanggal=data.tanggal,

        shift=data.shift,

        lokasi=data.lokasi,

        total_barang=data.total_barang,

        total_kebutuhan=data.total_kebutuhan,

        vendor_a_need=data.vendor_a_need,

        vendor_b_need=data.vendor_b_need
    )

    db.add(plan)

    db.commit()

    db.refresh(plan)

    return {
        "message": "Worker plan berhasil dibuat"
    }


# =========================
# GET WORKER PLAN
# =========================
@router.get("/worker-plan")
def get_worker_plan(

    tanggal: str,

    shift: str,

    db: Session = Depends(get_db)
):

    plan = db.query(models.WorkerPlan).filter(

        models.WorkerPlan.tanggal == tanggal,

        models.WorkerPlan.shift == shift

    ).first()

    if not plan:

        return {
            "message": "Plan tidak ditemukan"
        }



    return {

        "tanggal": plan.tanggal,

        "shift": plan.shift,

        "lokasi": plan.lokasi,

        "total_barang": plan.total_barang,

        "total_kebutuhan": plan.total_kebutuhan,

        "vendor_a_need": plan.vendor_a_need,

        "vendor_b_need": plan.vendor_b_need
    }

# =========================
# CREATE WORKER ATTENDANCE
# =========================
@router.post("/create-worker-attendance")
def create_worker_attendance(

    data: schemas.CreateWorkerAttendance,

    db: Session = Depends(get_db)
):
    
    # AMBIL WORKER PLAN
    plan = db.query(
        models.WorkerPlan
    ).filter(
        models.WorkerPlan.tanggal
        == data.tanggal,
        models.WorkerPlan.shift
        == data.shift
    ).first()

    if not plan:

        return {
            "message": "Plan tidak ditemukan"
        }
        

    success_ids = []
    duplicate_ids = []
    already_exists = []

    # TENTUKAN LIMIT VENDOR
    vendor_limit = 0
    if data.vendor == "Vendor A":
        vendor_limit = plan.vendor_a_need
    elif data.vendor == "Vendor B":
        vendor_limit = plan.vendor_b_need

    # HITUNG WORKER YANG SUDAH MASUK
    existing_count = db.query(
        models.WorkerAttendance
    ).filter(

        models.WorkerAttendance.tanggal
        == data.tanggal,

        models.WorkerAttendance.shift
        == data.shift,

        models.WorkerAttendance.vendor
        == data.vendor
        
    ).count()


    # HITUNG TOTAL SETELAH INPUT BARU
    new_worker_count = len(data.worker_ids)
    total_after_input = (
        existing_count +
        new_worker_count
    )

    # VALIDASI LIMIT PLAN
    # =========================
    if total_after_input > vendor_limit:
        return {
            "message":
            "Melebihi kebutuhan worker vendor",
            "vendor_limit": vendor_limit,
            "existing_worker": existing_count,
            "new_worker": new_worker_count,
            "total_after_input":
            total_after_input
        }


    for worker_id_input in data.worker_ids:

        # =========================
        # CEK DUPLICATE INPUT
        # =========================
        if worker_id_input in success_ids:
        
            duplicate_ids.append(worker_id_input)

            continue


        # CEK WORKER SUDAH MASUK SHIFT YANG SAMA
        existing_attendance = db.query(
            models.WorkerAttendance
        ).filter(
            models.WorkerAttendance.id_pekerja
            == worker_id_input,
            models.WorkerAttendance.tanggal
            == data.tanggal,
            models.WorkerAttendance.shift
            == data.shift
        ).first()
        if existing_attendance:
            already_exists.append(worker_id_input)
            continue


        # =========================
        # CARI ID PEKERJA
        # =========================
        worker_id_data = db.query(
            models.WorkerID
        ).filter(

            models.WorkerID.id_pekerja ==
            worker_id_input

        ).first()


        # =========================
        # SKIP JIKA TIDAK ADA
        # =========================
        if not worker_id_data:

            continue


        # =========================
        # SIMPAN ATTENDANCE
        # =========================
        attendance = models.WorkerAttendance(

            worker_id=worker_id_data.worker_id,

            id_pekerja=worker_id_input,

            tanggal=data.tanggal,

            shift=data.shift,

            vendor=data.vendor,

            lokasi=data.lokasi,

            attendance_type = "normal"
        )

        db.add(attendance)

        success_ids.append(worker_id_input)


    db.commit()


    return {

        "message": "Attendance berhasil disimpan",

        "total_success": len(success_ids),

        "success_ids": success_ids,

        "duplicate_ids": duplicate_ids,

        "already_exists": already_exists
    }

# =========================
# TAKEOUT WORKER
# =========================
@router.post("/takeout-worker")
def takeout_worker(

    data: schemas.TakeoutWorker,

    db: Session = Depends(get_db)
):

    # =========================
    # CARI ATTENDANCE
    # =========================
    attendance = db.query(
        models.WorkerAttendance
    ).filter(

        models.WorkerAttendance.id_pekerja
        == data.id_pekerja,

        models.WorkerAttendance.tanggal
        == data.tanggal,

        models.WorkerAttendance.shift
        == data.shift,

        models.WorkerAttendance.vendor
        == data.vendor

    ).first()


    # =========================
    # JIKA TIDAK ADA
    # =========================
    if not attendance:

        return {
            "message":
            "Worker attendance tidak ditemukan"
        }


    # =========================
    # DELETE ATTENDANCE
    # =========================
    db.delete(attendance)

    db.commit()


    return {

        "message":
        "Worker berhasil di-takeout",

        "id_pekerja":
        data.id_pekerja
    }

# =========================
# NONAKTIFKAN WORKER ID
# =========================
@router.post("/nonaktifkan-worker")
def nonaktifkan_worker(

    data: schemas.NonaktifkanWorker,

    db: Session = Depends(get_db)
):

    # =========================
    # CARI WORKER ID
    # =========================
    worker_id = db.query(

        models.WorkerID

    ).filter(

        models.WorkerID.id_pekerja
        == data.id_pekerja

    ).first()


    # =========================
    # JIKA TIDAK ADA
    # =========================
    if not worker_id:

        return {

            "success": False,

            "message":
            "ID pekerja tidak ditemukan"
        }


    # =========================
    # UPDATE STATUS
    # =========================
    worker_id.status = "inactive"


    # =========================
    # AMBIL DATA WORKER
    # =========================
    worker = db.query(

        models.Worker

    ).filter(

        models.Worker.id
        == worker_id.worker_id

    ).first()


    # =========================
    # SIMPAN KE
    # DISABLED WORKERS
    # =========================
    disabled_worker = (

        models.DisabledWorker(

            id_pekerja=
            worker_id.id_pekerja,

            nama_pekerja=
            worker.nama,

            vendor=
            worker.vendor,

            disabled_by=
            "Admin Gudang"
        )
    )


    db.add(
        disabled_worker
    )

    db.commit()


    return {

        "success": True,

        "message":
        "ID worker berhasil dinonaktifkan"
    }

# =========================
# GET ALL ATTENDANCES
# =========================
@router.get("/worker-attendances")
def get_worker_attendances(

    db: Session = Depends(get_db)
):

    attendances = db.query(
        models.WorkerAttendance
    ).all()


    results = []


    for attendance in attendances:

        worker = db.query(
            models.Worker
        ).filter(
            models.Worker.id
            == attendance.worker_id
        ).first()


        results.append({

            "id": attendance.id,

            "id_pekerja":
            attendance.id_pekerja,

            "nama":
            worker.nama,

            "tanggal":
            attendance.tanggal,

            "shift":
            attendance.shift,

            "vendor":
            attendance.vendor,

            "lokasi":
            attendance.lokasi
        })


    return results


# =========================
# CREATE BUFFER ATTENDANCE
# =========================
@router.post("/create-buffer-attendance")
def create_buffer_attendance(

    data: schemas.CreateBufferAttendance,

    db: Session = Depends(get_db)
):

    success_ids = []
    duplicate_ids = []
    already_exists = []


    for worker_id_input in data.worker_ids:

        # =========================
        # DUPLICATE INPUT
        # =========================
        if worker_id_input in success_ids:

            duplicate_ids.append(
                worker_id_input
            )

            continue


        # =========================
        # CEK SUDAH MASUK SHIFT
        # =========================
        existing_attendance = db.query(
            models.WorkerAttendance
        ).filter(

            models.WorkerAttendance
            .id_pekerja
            == worker_id_input,

            models.WorkerAttendance
            .tanggal
            == data.tanggal,

            models.WorkerAttendance
            .shift
            == data.shift

        ).first()


        if existing_attendance:

            already_exists.append(
                worker_id_input
            )

            continue


        # =========================
        # CARI WORKER ID
        # =========================
        worker_id_data = db.query(
            models.WorkerID
        ).filter(

            models.WorkerID.id_pekerja
            == worker_id_input

        ).first()


        # =========================
        # JIKA ID TIDAK ADA
        # =========================
        if not worker_id_data:

            continue


        # =========================
        # SIMPAN BUFFER
        # =========================
        attendance = models.WorkerAttendance(

            worker_id=
            worker_id_data.worker_id,

            id_pekerja=
            worker_id_input,

            tanggal=
            data.tanggal,

            shift=
            data.shift,

            vendor=
            data.vendor,

            lokasi=
            data.lokasi,

            attendance_type=
            "buffer"
        )


        db.add(attendance)

        success_ids.append(
            worker_id_input
        )


    db.commit()


    return {

        "message":
        "Buffer worker berhasil disimpan",

        "total_success":
        len(success_ids),

        "success_ids":
        success_ids,

        "duplicate_ids":
        duplicate_ids,

        "already_exists":
        already_exists
    }

# =========================
# UPLOAD FOTO KTP
# =========================
@router.post("/upload-ktp")
def upload_ktp(

    file: UploadFile = File(...)
):

    # =========================
    # BUAT FOLDER
    # =========================
    upload_folder = "uploads"

    os.makedirs(

        upload_folder,

        exist_ok=True
    )


    # =========================
    # SIMPAN FILE
    # =========================
    file_path = os.path.join(

        upload_folder,

        file.filename
    )


    with open(

        file_path,

        "wb"

    ) as buffer:

        shutil.copyfileobj(
            file.file,
            buffer
        )


    # =========================
    # OCR BACA GAMBAR
    # =========================
    image = Image.open(
        file_path
    )
    
    # PREPROCESS IMAGE
    image = image.convert(
        "L"
    )

    image = image.filter(
        ImageFilter.SHARPEN
    )

    enhancer = ImageEnhance.Contrast(
        image
    )

    image = enhancer.enhance(2)

    # OCR KHUSUS ANGKA
    text = pytesseract.image_to_string(
        image,

        config=
        "--psm 6"
    )

    # BERSIHKAN HASIL OCR
    cleaned_text = re.sub(

        r"[^0-9]",

        "",

        text
    )

    # AMBIL 16 DIGIT NIK
    # =========================
    nik_match = re.findall(
    
        r"\d{16}",
    
        cleaned_text
    )
    
    
    nik = nik_match[0] if nik_match else None

    return {
        "message":
        "Foto KTP berhasil diupload",

        "filename":
        file.filename,

        "ocr_result":
        text,

        "nik_detected":
        nik
    }


@router.post("/scan-ktp")
async def scan_ktp(
    file: UploadFile = File(...)
):

    try:

        contents = await file.read()

        np_arr = np.frombuffer(
            contents,
            np.uint8
        )

        image = cv2.imdecode(
            np_arr,
            cv2.IMREAD_COLOR
        )

        gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY
        )

        text = pytesseract.image_to_string(
            gray,
            lang="ind"
        )

        print("HASIL OCR:")
        print(text)


        # Cari angka 16 digit
        nik_match = re.search(
            r"\b\d{16}\b",
            text
        )

        if nik_match:

            nik = nik_match.group()

            return {
                "success": True,
                "nik": nik
            }

        return {
            "success": False,
            "message":
            "NIK tidak ditemukan"
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }