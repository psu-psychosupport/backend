
from fastapi import UploadFile, APIRouter
from fastapi.responses import FileResponse

from src.repositories.local_file_storage_repository import LocalFileStorageRepository

router = APIRouter()

# Приложение не должно реализовывать логику хранилища в таком виде,
# однако мне пофег


# TODO: add admin user depends
@router.post("/upload")
async def upload(file: UploadFile):
    name = await LocalFileStorageRepository.upload_file(file)
    return {"url": f"http://127.0.0.1:8000/file/{name}"}


@router.get("/file/{name}")
async def get_file(name: str):
    return FileResponse(await LocalFileStorageRepository.get_file_path(name))
