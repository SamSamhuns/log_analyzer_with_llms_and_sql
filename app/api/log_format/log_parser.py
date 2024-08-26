import logging
from typing import List
from datetime import datetime
from models.model import LogFileType


logger = logging.getLogger('log_format_api')


def gen_anomaly_detection_log_obj_list(log_file_content: str, logfile_id: str) -> List[dict]:
    """
    Generate log object list for anomaly detection log
    """
    log_obj_list = []
    log_lines = log_file_content.splitlines()
    log_lines_skipped = 0
    for log_line in log_lines:
        try:
            timestamp, inf_time, pred = log_line.split(",")
            iso_string = timestamp.strip().split()[0]
            timestamp = datetime.fromisoformat(iso_string.rstrip("Z")).strftime("%Y-%m-%d")
            inf_time = float(inf_time.strip().split()[-1][:-2])
            pred = int(pred.strip().split()[-1])

            log_obj = {"log_fid": logfile_id,
                       "timestamp": timestamp,
                       "inference_time": inf_time,
                       "prediction": pred}
            log_obj_list.append(log_obj)
        except Exception as excep:
            log_lines_skipped += 1

    logger.info("%d lines skipped due to errors.", log_lines_skipped)
    return log_obj_list


def gen_log_obj_list(log_file_content: str, logfile_id: str,  logfile_type: str) -> List[dict]:
    """
    Generate log object list based on the logfile type
    """
    if logfile_type not in LogFileType:
        raise NotImplementedError(f"logfile_type {logfile_type} not supported")
    
    if logfile_type == LogFileType.ANOMALY_DETECTION_LOG.value:
        log_obj_list = gen_anomaly_detection_log_obj_list(log_file_content, logfile_id)

    return log_obj_list


fpath = "/home/user/Main/log_summarizer/reference/$hypervisor-ml-rta-anomaly-detection-srta-q2-demo.log"
with open(fpath, "r") as f:
    log_file_content = f.read()
    log_obj_list = gen_log_obj_list(log_file_content,
                                    "1234567890", 
                                    LogFileType.ANOMALY_DETECTION_LOG.value)

    data_dicts = log_obj_list
    tb_name = LogFileType.ANOMALY_DETECTION_LOG.value

    col_names = ', '.join(data_dicts[0].keys())
    placeholders = ', '.join(['%s'] * len(data_dicts[0]))
    query = f"INSERT INTO {tb_name} ({col_names}) VALUES ({placeholders})".replace("'", '')

    # Prepare the list of tuples for insertion
    values = [tuple(data_dict.values()) for data_dict in data_dicts]
    breakpoint()