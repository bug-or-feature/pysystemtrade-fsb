from copy import copy

from sysdata.data_blob import dataBlob

from sysproduction.data.control_process import dataControlProcess
from sysproduction.data.control_process import diagControlProcess
from syscontrol.list_running_pids import describe_trading_server_login_data
from syscontrol.html_generation import (
    build_dashboard,
    build_report_files,
)


def monitor():
    with dataBlob(log_name="system-monitor") as data:
        data.log.debug("Starting process monitor...")
        process_observatory = processMonitor(data)
        check_if_pid_running_and_if_not_finish(process_observatory)
        process_observatory.update_all_status_with_process_control()
        build_dashboard(data, create_monitor_context(process_observatory))
        build_report_files(data, {})
        data.log.debug("Process monitor done.")


UNKNOWN_STATUS = "Unknown"

MAX_LOG_LENGTH = 17


class processMonitor(dict):
    def __init__(self, data):
        super().__init__()
        self._data = data
        # self._log_store = diagLogs(data)

        ## get initial status
        self.update_all_status_with_process_control()

    @property
    def data(self):
        return self._data

    @property
    def log_store(self):
        return self._log_store

    def process_dict_as_df(self):
        data_control = dataControlProcess(self.data)
        process_df = data_control.get_dict_of_control_processes().as_pd_df()
        return process_df

    def process_dict_to_html_table(self, file):
        data_control = dataControlProcess(self.data)
        dict_of_process = data_control.get_dict_of_control_processes()
        dict_of_process.to_html_table_in_file(file)

    def update_all_status_with_process_control(self):
        list_of_process = get_list_of_process_names(self)
        for process_name in list_of_process:
            process_running_status = get_running_mode_str_for_process(
                self, process_name
            )
            self.update_status(process_name, process_running_status)

    def update_status(self, process_name, new_status):
        current_status = self.get_current_status(process_name)
        if current_status == new_status:
            pass
        else:
            self.change_status(process_name, new_status)

    def change_status(self, process_name, new_status):
        self[process_name] = new_status

    def get_current_status(self, process_name):
        status = copy(self.get(process_name, UNKNOWN_STATUS))
        return status

    def get_recent_log_messages(self):
        # msgs = [
        #     entry.text
        #     for entry in self.log_store.get_log_items(
        #         attribute_dict={"sysmon": "status_change"}
        #     )
        # ]
        msgs = []
        return msgs


def get_list_of_process_names(process_observatory: processMonitor):
    diag_control = diagControlProcess(process_observatory.data)
    return diag_control.get_list_of_process_names()


def get_running_mode_str_for_process(
    process_observatory: processMonitor, process_name: str
):
    control = get_control_for_process(process_observatory, process_name)
    return control.running_mode_str


def get_control_for_process(process_observatory: processMonitor, process_name: str):
    diag_control = diagControlProcess(process_observatory.data)
    control = diag_control.get_control_for_process_name(process_name)

    return control


def check_if_pid_running_and_if_not_finish(process_observatory: processMonitor):
    data_control = dataControlProcess(process_observatory.data)
    data_control.check_if_pid_running_and_if_not_finish_all_processes()


def create_monitor_context(process_observatory):
    return {
        "trading_server_description": describe_trading_server_login_data(),
        "dbase_description": str(process_observatory.data.mongo_db),
        "process_info": process_observatory.process_dict_as_df(),
        "log_messages": process_observatory.get_recent_log_messages()[-MAX_LOG_LENGTH:],
    }


if __name__ == "__main__":
    monitor()
