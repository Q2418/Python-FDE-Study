import logging

logger = logging.getLogger("asset_admin")


def log_operation(user, action: str, detail: str = "") -> None:
    """关键操作日志：登录、增删改、领用归还、AI 调用等"""
    username = getattr(user, "username", None) or "-"
    logger.info("[操作日志] 用户=%s 动作=%s 详情=%s", username, action, detail)
