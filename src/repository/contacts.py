from sqlalchemy import select, and_, extract, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.entity.models import Contact, User
from src.schemas.contact import ContactCreateSchema, ContactUpdateSchema
from datetime import date, timedelta

async def get_contacts(limit: int, offset: int, first_name: str, last_name: str,
                       email: str, db: AsyncSession, user: User):
    stmt = select(Contact).filter_by(user=user).offset(offset).limit(limit)
    if first_name or last_name or email:
        stmt = stmt.filter(
            and_(
                first_name is None or Contact.first_name.ilike(
                    f"%{first_name}%"),
                last_name is None or Contact.last_name.ilike(f"%{last_name}%"),
                email is None or Contact.email.ilike(f"%{email}%"),
            )
        )
    contacts = await db.execute(stmt)
    return contacts.scalars().all()


async def get_contact(contact_id: int, db: AsyncSession, user: User):
    stmt = select(Contact).filter_by(id=contact_id, user=user)
    contact = await db.execute(stmt)
    return contact.scalar_one_or_none()


async def create_contact(body: ContactCreateSchema, db: AsyncSession, user: User):
    contact = Contact(**body.model_dump(exclude_unset=True), user=user)
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


async def update_contact(contact_id: int, body: ContactUpdateSchema,
                         db: AsyncSession, user: User):
    stmt = select(Contact).filter_by(id=contact_id, user=user)
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()
    if contact:
        for key, value in body.model_dump(exclude_unset=True).items():
            setattr(contact, key, value)
        await db.commit()
        await db.refresh(contact)
    return contact


async def delete_contact(contact_id: int, db: AsyncSession, user: User):
    stmt = select(Contact).filter_by(id=contact_id, user=user)
    contact = await db.execute(stmt)
    contact = contact.scalar_one_or_none()
    if contact:
        await db.delete(contact)
        await db.commit()
    return contact


async def get_upcoming_birthdays(db: AsyncSession, user: User):
    try:
        today = date.today()
        end_date = today + timedelta(days=7)

        # Обробка дат у форматі MM-DD для врахування місяця та дня
        stmt = select(Contact).filter(
            and_(
                func.to_char(Contact.birthday, 'MM-DD') >= func.to_char(today, 'MM-DD'),
                func.to_char(Contact.birthday, 'MM-DD') <= func.to_char(end_date, 'MM-DD'),
                Contact.user == user  # Додаємо фільтр для перевірки користувача
            )
        )
        result = await db.execute(stmt)
        contacts = result.scalars().all()
        return contacts
    except Exception as e:
        raise Exception(f"Error fetching upcoming birthdays: {e}")
