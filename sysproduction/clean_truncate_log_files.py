from sysproduction._DEPRECATED.logs import diagLogs
from sysdata.data_blob import dataBlob


def clean_truncate_log_files():
    data = dataBlob()
    cleaner = cleanTruncateLogFiles(data)
    cleaner.clean_log_files()
    return None


class cleanTruncateLogFiles:
    def __init__(self, data: dataBlob):
        self.data = data

    ## FIXME - CHANGE TO FILE ROTATION
    def clean_log_files(self):
        mlog = diagLogs(self.data)
        self.data.log.debug("Deleting log items more than 14 days old")
        mlog.delete_log_items_from_before_n_days(days=14)


if __name__ == "__main__":
    clean_truncate_log_files()
