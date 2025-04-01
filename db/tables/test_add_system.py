from typing import Optional
from sqlalchemy.orm import Session

from db.session import SessionLocal
from db.tables.systems import SystemsTable
from db.session import get_db
from utils.log import logger


def create_system(db_session: Session, host: str, user: str, password: str, port: int, schema: str) -> SystemsTable:
    """
    Create a new system in the database.

    Args:
        db_session (Session): The SQLAlchemy session to use.
        host (str): The host of the system.
        user (str): The user for the system.
        password (str): The password for the system.
        port (int): The port of the system.
        schema (str): The schema of the system.

    Returns:
        SystemsTable: The created system object.
    """
    try:
        new_system = SystemsTable(
            host=host,
            user=user,
            password=password,
            port=port,
            schema=schema
        )
        db_session.add(new_system)
        db_session.commit()
        db_session.refresh(new_system)
        return new_system
    except Exception as e:
        logger.error(f"Error creating system: {e}")
        db_session.rollback()
        raise
    
def get_system(db_session: Session, host: str) -> Optional[SystemsTable]:
    return db_session.query(SystemsTable).filter(SystemsTable.host == host).first()

if __name__ == "__main__":
    with SessionLocal() as session, session.begin():
        logger.info("Creating system...")
        create_system(
            session,
            host="myhost",
            user="admin",
            password="password",
            port=5432,
            schema="public"
        )
        logger.info("System created successfully.")
        logger.info("Fetching system...")
        system = get_system(session, host="myhost")
        if system:
            logger.info(f"System found: {system.host}, {system.user}, {system.password}, {system.port}, {system.schema}")
        else:
            logger.info("System not found.")
        
        
    