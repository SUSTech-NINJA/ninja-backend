# Database

根据需求，我们创建了四张表用于存储用户信息、机器人信息和会话历史记录。

## User

User 表存储用户的用户名，密码、设置、余额和主页信息。

- `id`: 用户的UUID。除登陆操作外，所有的操作都需要用户的UUID。
- `username`: 用户名，全局唯一。
- `password`: 哈希后的密码。
- `settings`: 用户的设置，格式为JSON，见[Settings](#Settings)。
- `current`: 用户的余额。

### Settings

## Session

## Bot

## Chat


