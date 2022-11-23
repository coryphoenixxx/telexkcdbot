
CREATE TABLE IF NOT EXISTS comics (
                     id SERIAL NOT NULL,
                     comic_id INTEGER NOT NULL UNIQUE,
                     title VARCHAR(128) DEFAULT '...',
                     img_url VARCHAR(512) DEFAULT '',
                     comment TEXT DEFAULT '...',
                     public_date DATE NOT NULL DEFAULT CURRENT_DATE,
                     is_specific BOOLEAN DEFAULT FALSE,
                     ru_title VARCHAR(128) DEFAULT '...',
                     ru_img_url VARCHAR(512) DEFAULT '...',
                     ru_comment TEXT DEFAULT '...',
                     has_ru_translation BOOLEAN DEFAULT FALSE);

                   CREATE UNIQUE INDEX IF NOT EXISTS comic_id_uindex ON comics (comic_id);

CREATE TABLE IF NOT EXISTS users (
                     id SERIAL NOT NULL,
                     user_id INTEGER UNIQUE,
                     user_lang VARCHAR(2) DEFAULT 'en',
                     last_comic_info VARCHAR(10) DEFAULT '0_en',
                     bookmarks JSON DEFAULT '[]',
                     notification_sound_status BOOLEAN DEFAULT FALSE,
                     lang_btn_status BOOLEAN DEFAULT TRUE,
                     is_banned BOOLEAN DEFAULT FALSE,
                     only_ru_mode BOOLEAN DEFAULT FALSE,
                     last_action_date DATE DEFAULT CURRENT_DATE);

                   CREATE UNIQUE INDEX IF NOT EXISTS user_id_uindex ON users (id);
