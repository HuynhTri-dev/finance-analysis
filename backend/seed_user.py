"""
name: seed_user.py
description: CLI utility script for creating, updating, and managing user accounts
             directly in the PostgreSQL database.
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from sqlalchemy import select

from app.core.security import hash_password
from app.infra.database import async_session_maker, engine
from app.models import Base, User


async def create_or_update_user(username: str, password: str, full_name: str = "Quản Trị Viên", is_active: bool = True) -> None:
    """
    Creates a new user or updates the password/details of an existing user.
    """
    username = username.strip()
    if not username or not password:
        print("❌ Error: Username and password must not be empty.")
        return

    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as session:
        stmt = select(User).where(User.username == username)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        hashed = hash_password(password)

        if user:
            user.hashed_password = hashed
            user.full_name = full_name
            user.is_active = is_active
            await session.commit()
            print(f"✅ Đã cập nhật thành công mật khẩu cho tài khoản: '{username}' (Tên: {full_name})")
        else:
            new_user = User(
                username=username,
                hashed_password=hashed,
                full_name=full_name,
                is_active=is_active,
            )
            session.add(new_user)
            await session.commit()
            print(f"✅ Đã tạo mới thành công tài khoản: '{username}' (Tên: {full_name})")

    await engine.dispose()


async def list_users() -> None:
    """Lists all user accounts in the database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as session:
        stmt = select(User)
        result = await session.execute(stmt)
        users = result.scalars().all()

        if not users:
            print("ℹ️ Chưa có tài khoản nào trong cơ sở dữ liệu.")
            await engine.dispose()
            return

        print(f"\n📋 Danh sách người dùng trong hệ thống ({len(users)} tài khoản):")
        print("-" * 65)
        print(f"{'Username':<20} | {'Tên hiển thị':<25} | {'Trạng thái':<10}")
        print("-" * 65)
        for u in users:
            status = "Hoạt động" if u.is_active else "Tạm khóa"
            print(f"{u.username:<20} | {u.full_name:<25} | {status:<10}")
        print("-" * 65 + "\n")

    await engine.dispose()



def main() -> None:
    parser = argparse.ArgumentParser(description="Quản lý tài khoản người dùng trực tiếp từ Database.")
    parser.add_argument("--username", "-u", type=str, help="Tên đăng nhập")
    parser.add_argument("--password", "-p", type=str, help="Mật khẩu tài khoản")
    parser.add_argument("--name", "-n", type=str, default="Quản Trị Viên", help="Tên hiển thị người dùng")
    parser.add_argument("--list", "-l", action="store_true", help="Liệt kê danh sách tất cả tài khoản")

    args = parser.parse_args()

    if args.list:
        asyncio.run(list_users())
    elif args.username and args.password:
        asyncio.run(create_or_update_user(args.username, args.password, args.name))
    else:
        # Default prompt mode if no args given
        print("💡 Chế độ dòng lệnh quản lý tài khoản DB:")
        print("   Tạo/cập nhật: python seed_user.py --username admin --password yourpassword --name 'Admin'")
        print("   Xem danh sách: python seed_user.py --list\n")
        u = input("Nhập Username [mặc định: admin]: ").strip() or "admin"
        p = input(f"Nhập Mật khẩu cho '{u}': ").strip()
        if not p:
            print("❌ Mật khẩu không được để trống.")
            sys.exit(1)
        n = input("Nhập Tên hiển thị [mặc định: Quản Trị Viên]: ").strip() or "Quản Trị Viên"
        asyncio.run(create_or_update_user(u, p, n))


if __name__ == "__main__":
    main()
