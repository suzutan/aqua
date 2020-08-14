import sqlalchemy
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.automap import automap_base

# mysqlのDBの設定
engine = sqlalchemy.create_engine('mysql+pymysql://root:mysql@localhost:3306/yt_video?charset=utf8mb4', echo=True)

# Sessionの作成
Session = scoped_session(
    # ORM実行時の設定。自動コミットするか、自動反映するなど。
    sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
)
Base = automap_base()
