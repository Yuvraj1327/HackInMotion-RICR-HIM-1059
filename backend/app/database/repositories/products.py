from app.database.repositories.base import BaseRepository


class ProductRepository(BaseRepository):
    table_name = "products"
