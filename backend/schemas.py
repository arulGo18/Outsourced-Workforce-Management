from pydantic import BaseModel

class LoginRequest(BaseModel):
    vendor: str
    pic: str
    password: str

class LoginResponse(BaseModel):
    vendor: str
    pic: str
    lokasi_gudang: str
    status: str


class CreateWorker(BaseModel):
    nama: str
    nik: str
    no_kk: str
    jenis_kelamin: str
    alamat: str
    email: str
    no_hp: str
    vendor: str
    departemen: str
    nama_rekening: str
    no_rekening: str
    bank: str
    tipe_kontrak: str

class ActivateWorker(BaseModel):
    id_pekerja: str
    placement_id: int

class MutasiWorker(BaseModel):
    id_pekerja: str
    placement_id: int

class EditContract(BaseModel):
    id_pekerja: str
    tipe_kontrak: str
    departemen: str

class CreateWorkerPlan(BaseModel):
    tanggal: str
    shift: str
    lokasi: str
    total_barang: int
    total_kebutuhan: int
    vendor_a_need: int
    vendor_b_need: int

class CreateWorkerAttendance(BaseModel):
    tanggal: str
    shift: str
    vendor: str
    lokasi: str
    worker_ids: list[str]

class TakeoutWorker(BaseModel):
    tanggal: str
    shift: str
    vendor: str
    id_pekerja: str

class NonaktifkanWorker(BaseModel):
     id_pekerja: str

class AdminLogin(BaseModel):
    admin_id: str
    password: str

class CreateBufferAttendance(BaseModel):

    tanggal: str

    shift: str

    vendor: str

    lokasi: str

    worker_ids: list[str]