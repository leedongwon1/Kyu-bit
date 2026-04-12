# api/exceptions.py
"""Kyu-bit 커스텀 예외 클래스"""

class KyuBitError(Exception):
    """Kyu-bit 기본 예외"""
    pass

class QUBOGenerationError(KyuBitError):
    """QUBO 행렬 생성 실패"""
    pass

class SolverTimeoutError(KyuBitError):
    """솔버 실행 시간 초과"""
    pass

class InvalidCropKeyError(KyuBitError):
    """존재하지 않는 작물 키"""
    pass

class InvalidFarmSizeError(KyuBitError):
    """잘못된 밭 크기 (0 이하)"""
    pass