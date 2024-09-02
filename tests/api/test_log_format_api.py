"""
Test milvus api
The milvus server must be running in the appropriate port 
"""
import json
import pytest
from app.models.model import LogFileType
from app.api.log_format.log_parser import(
    gen_anomaly_detection_log_obj_list,
    gen_log_obj_list)


def test_gen_anomaly_detection_log_obj_list_valid_from_file(mock_one_anomaly_detection_log_file_content):
    """Test the gen_anomaly_detection_log_obj_list function with valid input from log file"""
    logfile_id = "12345"
    _, content = mock_one_anomaly_detection_log_file_content
    enc = json.detect_encoding(content)
    file_content_str = content.decode(enc)
    result = gen_anomaly_detection_log_obj_list(file_content_str, logfile_id)

    assert len(result) == 587


def test_gen_anomaly_detection_log_obj_list_valid(mock_valid_anomaly_det_log_str):
    """Test the gen_anomaly_detection_log_obj_list function with valid input"""
    logfile_id = "12345"
    result = gen_anomaly_detection_log_obj_list(mock_valid_anomaly_det_log_str, logfile_id)
    assert len(result) == 2
    assert result[0]['log_fid'] == logfile_id
    assert result[0]['timestamp'] == "2024-01-01"
    assert result[0]['inference_time'] == 100.0
    assert result[0]['prediction'] == 1


def test_gen_anomaly_detection_log_obj_list_invalid(mock_invalid_anomaly_det_log_str):
    """Test the gen_anomaly_detection_log_obj_list function with invalid input"""
    logfile_id = "12345"
    result = gen_anomaly_detection_log_obj_list(mock_invalid_anomaly_det_log_str, logfile_id)
    # Assuming that the incorrect line will be skipped
    assert len(result) == 1
    assert result[0]['log_fid'] == logfile_id


def test_gen_log_obj_list_supported_type(mock_valid_anomaly_det_log_str):
    """Test the gen_log_obj_list function with a supported log type"""
    logfile_id = "12345"
    result = gen_log_obj_list(mock_valid_anomaly_det_log_str, logfile_id, LogFileType.ANOMALY_DETECTION_LOG.value)
    assert len(result) == 2
    assert result[0]['prediction'] == 1


def test_gen_log_obj_list_unsupported_type():
    """Test the gen_log_obj_list function with an unsupported log type"""
    logfile_id = "12345"
    with pytest.raises(NotImplementedError):
        gen_log_obj_list("PLACEHOLDER", logfile_id, "UNSUPPORTED_LOG_TYPE")
