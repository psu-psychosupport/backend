from typing import Optional

from sqlalchemy import ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects import postgresql

from src.database.base import BaseTable, int_pk, str_128
from src.models.enums import MediaTypes, PersonalInformationTypes
from src.models.schemas.content import (
    CategorySchema,
    MediaFileSchema, SubCategorySchema,
    PostSchema,
    PersonalInformationSchema,
)
from src.models.tables.users import UserTable


class CategoryTable(BaseTable):
    __tablename__ = "categories"

    id: Mapped[int_pk]
    name: Mapped[str_128]

    subcategories: Mapped[list["SubCategoryTable"]] = relationship(
        back_populates="category",
        lazy="noload",
    )
    post: Mapped[Optional["PostTable"]] = relationship(
        back_populates="category",
        lazy="noload",
        primaryjoin="and_(CategoryTable.id == PostTable.category_id, PostTable.subcategory_id == None)"
    )
 
    def to_schema_model(self, *, load_subcategories: bool = True, load_post: bool = True):
        return CategorySchema(
            id=self.id,
            name=self.name,
            subcategories=[subcategory.to_schema_model(load_category=False) for subcategory in self.subcategories] if load_subcategories and self.subcategories else [],
            post=self.post.to_schema_model(load_category=False, load_subcategory=False) if load_post and self.post else None,
        )


class SubCategoryTable(BaseTable):
    __tablename__ = "subcategories"

    id: Mapped[int_pk]
    category_id: Mapped[int] = mapped_column(ForeignKey(CategoryTable.id, ondelete="CASCADE"))
    name: Mapped[str_128]

    category: Mapped["CategoryTable"] = relationship(
        back_populates="subcategories",
        lazy="noload",
    )
    post: Mapped["PostTable"] = relationship(back_populates="subcategory", lazy="noload")

    def to_schema_model(self, *, load_post: bool = True, load_category: bool = True):
        return SubCategorySchema(
            id=self.id,
            category_id=self.category_id,
            name=self.name,
            category=self.category.to_schema_model(load_subcategories=False, load_post=False) if load_category and self.category else None,
            post=self.post.to_schema_model(load_category=False, load_subcategory=False) if load_post and self.post else None,
        )


class PostTable(BaseTable):
    __tablename__ = "posts"

    id: Mapped[int_pk]
    category_id: Mapped[int] = mapped_column(ForeignKey(CategoryTable.id), default=None)
    subcategory_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey(SubCategoryTable.id),
        nullable=True,
        default=None
    )
    content: Mapped[str] = mapped_column(Text, default=None)
    views: Mapped[int] = mapped_column(default=0)

    category: Mapped["CategoryTable"] = relationship(back_populates="post", lazy="joined")
    subcategory: Mapped[Optional["SubCategoryTable"]] = relationship(back_populates="post", lazy="joined")

    __table_args__ = (
        UniqueConstraint("category_id", "subcategory_id", name="unique_post"),
    )

    def to_schema_model(self, *, load_category: bool = True, load_subcategory: bool = True):
        return PostSchema(
            id=self.id,
            category_id=self.category_id,
            subcategory_id=self.subcategory_id,
            content=self.content,
            views=self.views,
            category=self.category.to_schema_model(load_post=False, load_subcategories=False) if load_category and self.category else None,
            subcategory=self.subcategory.to_schema_model(load_post=False, load_category=False) if load_subcategory and self.subcategory else None
        )


class MediaFileTable(BaseTable):
    __tablename__ = "media_files"

    id: Mapped[int_pk]
    type: Mapped[int]
    file_name: Mapped[Optional[str_128]] = mapped_column(default=None)
    file_url: Mapped[Optional[str_128]] = mapped_column(default=None)
    data: Mapped[Optional[str]] = mapped_column(Text, default=None)

    def to_schema_model(self, is_nested: bool = False):
        return MediaFileSchema(
            id=self.id,
            file_name=self.file_name,
            file_url=self.file_url,
            type=MediaTypes(self.type),
            data=self.data,
        )


class PersonalInformationTable(BaseTable):
    __tablename__ = "personal_information"

    id: Mapped[int_pk]
    informational_content_id: Mapped[int] = mapped_column(ForeignKey(PostTable.id))
    user_id: Mapped[int] = mapped_column(ForeignKey(UserTable.id))
    content_type: Mapped[PersonalInformationTypes] = mapped_column(
        postgresql.ENUM(PersonalInformationTypes)
    )
    content: Mapped[Optional[str]]

    def to_schema_model(self, is_nested: bool = False):
        return PersonalInformationSchema(
            id=self.id,
            informational_content_id=self.informational_content_id,
            user_id=self.user_id,
            content_type=self.content_type,
            content=self.content,
        )
