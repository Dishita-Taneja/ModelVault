import datetime
from dateutil import parser
from typing import Dict, Any, Optional
from app.schemas.event import NormalizedEventCreate


def parse_datetime(dt_val: Any) -> datetime.datetime:
    if isinstance(dt_val, datetime.datetime):
        return dt_val
    return parser.parse(str(dt_val))


def map_arn_to_username(arn: str) -> Optional[str]:
    if not arn:
        return None
    if "/" in arn:
        return arn.split("/")[-1]
    return arn


def normalize_iam_log(raw: Dict[str, Any], user_map: Dict[str, str]) -> NormalizedEventCreate:
    ts = parse_datetime(raw["timestamp"])
    arn = raw.get("user_arn", "")
    username = map_arn_to_username(arn)
    user_id = user_map.get(username) if username else None

    extra = {
        "user_agent": raw.get("user_agent"),
        "status": raw.get("status", "SUCCESS"),
        "raw_payload": raw
    }

    return NormalizedEventCreate(
        event_id=raw["event_id"],
        source="IAM",
        event_time_raw=ts,
        event_time_reconciled=ts,  # Reconciled baseline matches raw timestamp
        user_id=user_id,
        user_name=arn,
        ip_address=raw.get("source_ip"),
        event_name=raw.get("action", "IAMAction"),
        model_id=None,
        region="us-east-1",
        status=raw.get("status", "SUCCESS"),
        bytes_transferred=0,
        risk_score=0.0,
        anomaly_flag=False,
        extra=extra
    )


def normalize_ec2_log(raw: Dict[str, Any], ip_user_map: Dict[str, str]) -> NormalizedEventCreate:
    ts = parse_datetime(raw["timestamp"])
    ip = raw.get("source_ip")
    user_id = ip_user_map.get(ip) if ip else None

    extra = {
        "instance_id": raw.get("instance_id"),
        "status": raw.get("status", "SUCCESS"),
        "raw_payload": raw
    }

    return NormalizedEventCreate(
        event_id=raw["event_id"],
        source="EC2",
        event_time_raw=ts,
        event_time_reconciled=ts,
        user_id=user_id,
        user_name=None,
        ip_address=ip,
        event_name=raw.get("action", "EC2Action"),
        model_id=None,
        region="us-east-1",
        status=raw.get("status", "SUCCESS"),
        bytes_transferred=int(raw.get("bytes_transferred", 0)),
        risk_score=0.0,
        anomaly_flag=False,
        extra=extra
    )


def normalize_s3_log(
    raw: Dict[str, Any],
    user_map: Dict[str, str],
    s3_model_map: Dict[str, str]
) -> NormalizedEventCreate:
    ts = parse_datetime(raw["timestamp"])
    arn = raw.get("requester_arn", "")
    username = map_arn_to_username(arn)
    user_id = user_map.get(username) if username else None
    
    key = raw.get("key", "")
    s3_uri = f"s3://{raw.get('bucket', '')}/{key}" if key else ""
    model_id = s3_model_map.get(s3_uri) or s3_model_map.get(key)

    extra = {
        "bucket": raw.get("bucket"),
        "key": key,
        "http_status": raw.get("http_status", 200),
        "raw_payload": raw
    }

    return NormalizedEventCreate(
        event_id=raw["event_id"],
        source="S3",
        event_time_raw=ts,
        event_time_reconciled=ts,
        user_id=user_id,
        user_name=arn,
        ip_address=raw.get("source_ip"),
        event_name="GetObject",
        model_id=model_id,
        region="us-east-1",
        status="SUCCESS" if raw.get("http_status", 200) == 200 else "FAILED",
        bytes_transferred=int(raw.get("bytes_sent", 0)),
        risk_score=0.0,
        anomaly_flag=False,
        extra=extra
    )


def normalize_model_access_log(raw: Dict[str, Any], user_map: Dict[str, str]) -> NormalizedEventCreate:
    ts = parse_datetime(raw["timestamp"])
    arn = raw.get("requester_arn", "")
    username = map_arn_to_username(arn)
    user_id = user_map.get(username) if username else None

    extra = {
        "input_tokens": raw.get("input_tokens", 0),
        "execution_time_ms": raw.get("execution_time_ms", 0),
        "raw_payload": raw
    }

    return NormalizedEventCreate(
        event_id=raw["event_id"],
        source="MODEL",
        event_time_raw=ts,
        event_time_reconciled=ts,
        user_id=user_id,
        user_name=arn,
        ip_address=None,
        event_name="InvokeEndpoint",
        model_id=raw.get("model_id"),
        region="us-east-1",
        status=raw.get("status", "SUCCESS"),
        bytes_transferred=0,
        risk_score=0.0,
        anomaly_flag=False,
        extra=extra
    )
