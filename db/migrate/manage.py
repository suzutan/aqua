#!/usr/bin/env python
from migrate.versioning.shell import main

if __name__ == '__main__':
    main(url='mysql+pymysql://root:mysql@localhost:3306/yt_video?charset=utf8mb4', repository='.', debug='False')
