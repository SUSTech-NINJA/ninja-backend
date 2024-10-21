# Backend Design Document

# API Design

TBD

# Database

[](https://github.com/SUSTech-NINJA/ninja-backend/blob/d37980c9e5caa97fd89247dfeb019c42a135a50e/docs/schema.sql#L1-L37)

根据需求，我们创建了四张表用于存储用户信息、机器人信息和会话历史记录。

## User

User 表存储用户的用户名，密码、设置、余额和主页信息。

- `id`: `String`, 用户的UUID。除登陆操作外，所有的操作都需要用户的UUID。
- `username`: `String`, 用户名，全局唯一。
- `password`: `String`, 哈希后的密码。
- `settings`: `JSON`, 用户的设置，见[Settings](#Settings)。
- `current`: `int`, 用户的余额。
- `credit`: `JSON`, 用户的模型用量余额。
- `comments`: `JSON`, 用户收到的评论。
- `posts`: `JSON`, 用户的帖子。
- `query`: `JSON`, 用户收到的询问。

### Settings

TBD

## Session

Session 表存储用户登陆的tokens。

- `id`: `String`, 用户的UUID, 引用User表。
- `token`: `String`, 用户的token。
- `expiry`: `String`, token的过期时间。

## Bot

Bot 表存储机器人的信息, 包括机器人的名字、模型、访问API、余额和主页信息。

- `id`: 
- `base_model` TEXT,
- `url` TEXT,
- `usage_limit` INTEGER,
- `price` INTEGER

## Chat

Chat 表存储用户的会话历史和对应的设置信息。

- `id`
- `user_id` TEXT,
- `title` TEXT,
- `settings` JSON,
- `history` JSON,

### Chat Settings

TBD
