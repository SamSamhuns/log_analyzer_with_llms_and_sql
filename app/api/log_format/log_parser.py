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
    for i, log_line in enumerate(log_lines):
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
            logger.debug("Skipped line %d due to error: %s", i, excep)
            log_lines_skipped += 1

    logger.info("%d lines skipped due to errors.", log_lines_skipped)
    return log_obj_list


def gen_rta_worker_switch_log_obj_list(log_file_content: str, logfile_id: str) -> List[dict]:
    """
    Generate log object list for rta worker switch log
    """
    log_obj_list = []
    log_lines = log_file_content.splitlines()
    log_lines_skipped = 0
    for log_line in log_lines:
        try:
            timestamp_and_goal_type, rta_status = log_line.split(",")
            timestamp = timestamp_and_goal_type.split()[0]
            iso_string = timestamp.strip().split()[0]
            timestamp = datetime.fromisoformat(iso_string.rstrip("Z")).strftime("%Y-%m-%d")
            goal_type = timestamp_and_goal_type.split()[-1][1:-1]
            rta_status = int(rta_status.strip().split()[-1][1:-1])

            log_obj = {"log_fid": logfile_id,
                       "timestamp": timestamp,
                       "goal_type": goal_type,
                       "rta_status": rta_status}
            log_obj_list.append(log_obj)
        except Exception as excep:
            log_lines_skipped += 1

    logger.info("%d lines skipped due to errors.", log_lines_skipped)
    return log_obj_list


def gen_log_obj_list(log_file_content: str, logfile_id: str, logfile_type: str) -> List[dict]:
    """
    Generate log object list based on the logfile type
    """
    if logfile_type not in set(item.value for item in LogFileType):
        raise NotImplementedError(f"logfile_type {logfile_type} not supported")

    if logfile_type == LogFileType.ANOMALY_DETECTION_LOG.value:
        log_obj_list = gen_anomaly_detection_log_obj_list(log_file_content, logfile_id)
    elif logfile_type == LogFileType.RTA_WORKER_SWITCH_LOG.value:
        log_obj_list = gen_rta_worker_switch_log_obj_list(log_file_content, logfile_id)

    return log_obj_list
