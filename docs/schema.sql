-- This file is deprecated. Only for reference purposes.

CREATE TABLE user (
    id TEXT PRIMARY KEY DEFAULT( uuid() ),
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    settings JSON NOT NULL,
    balance INTEGER NOT NULL,
    credit JSON NOT NULL,
    comments JSON NOT NULL,
    posts JSON NOT NULL,
    query JSON NOT NULL
);

CREATE TABLE session (
    user_id INTEGER NOT NULL,
    token TEXT NOT NULL,
    expiry TIMESTAMP NOT NULL,
    FOREIGN KEY(user_id) REFERENCES user(id)
);

CREATE TABLE bot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    base_model TEXT NOT NULL,
    url TEXT NOT NULL,
    usage_limit INTEGER NOT NULL,
    price INTEGER NOT NULL,
    is_default BOOLEAN NOT NULL
);

CREATE TABLE chat (
    id TEXT PRIMARY KEY DEFAULT( uuid() ),
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    settings JSON NOT NULL,
    history JSON NOT NULL,
    FOREIGN KEY(user_id) REFERENCES user(id)
);
