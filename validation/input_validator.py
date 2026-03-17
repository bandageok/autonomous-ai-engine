"""Input Validator - 输入验证器"""
import re
import logging
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """验证级别"""
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationType(Enum):
    """验证类型"""
    REQUIRED = "required"
    TYPE = "type"
    RANGE = "range"
    LENGTH = "length"
    PATTERN = "pattern"
    CUSTOM = "custom"
    SCHEMA = "schema"


@dataclass
class ValidationError:
    """验证错误"""
    field: str
    message: str
    level: ValidationLevel
    validation_type: ValidationType
    value: Any = None
    expected: Any = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "field": self.field,
            "message": self.message,
            "level": self.level.value,
            "validation_type": self.validation_type.value,
            "value": str(self.value) if self.value is not None else None,
            "expected": str(self.expected) if self.expected is not None else None,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class ValidationResult:
    """验证结果"""
    valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    validated_data: Dict = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)
    
    def add_error(self, error: ValidationError):
        """添加错误"""
        if error.level == ValidationLevel.WARNING:
            self.warnings.append(error)
        else:
            self.errors.append(error)
            self.valid = False
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "valid": self.valid,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "validated_data": self.validated_data,
            "metadata": self.metadata
        }
    
    def to_json(self) -> str:
        """转换为JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class ValidationRule:
    """验证规则基类"""
    
    def __init__(
        self,
        name: str,
        validation_type: ValidationType,
        level: ValidationLevel = ValidationLevel.ERROR,
        message: str = "",
        field: str = ""
    ):
        self.name = name
        self.validation_type = validation_type
        self.level = level
        self.message = message
        self.field = field
    
    def validate(self, value: Any, data: Dict) -> Optional[ValidationError]:
        """验证值"""
        raise NotImplementedError


class RequiredRule(ValidationRule):
    """必填验证规则"""
    
    def __init__(self, field: str, message: str = ""):
        super().__init__(
            name=f"required_{field}",
            validation_type=ValidationType.REQUIRED,
            field=field,
            message=message or f"Field '{field}' is required"
        )
    
    def validate(self, value: Any, data: Dict) -> Optional[ValidationError]:
        """验证值"""
        if value is None or value == "" or (isinstance(value, list) and len(value) == 0):
            return ValidationError(
                field=self.field,
                message=self.message,
                level=self.level,
                validation_type=self.validation_type,
                value=value
            )
        return None


class TypeRule(ValidationRule):
    """类型验证规则"""
    
    def __init__(
        self,
        field: str,
        expected_type: type,
        message: str = ""
    ):
        super().__init__(
            name=f"type_{field}",
            validation_type=ValidationType.TYPE,
            field=field,
            message=message or f"Field '{field}' must be of type {expected_type.__name__}"
        )
        self.expected_type = expected_type
    
    def validate(self, value: Any, data: Dict) -> Optional[ValidationError]:
        """验证值"""
        if value is not None and not isinstance(value, self.expected_type):
            return ValidationError(
                field=self.field,
                message=self.message,
                level=self.level,
                validation_type=self.validation_type,
                value=type(value).__name__,
                expected=self.expected_type.__name__
            )
        return None


class LengthRule(ValidationRule):
    """长度验证规则"""
    
    def __init__(
        self,
        field: str,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        message: str = ""
    ):
        super().__init__(
            name=f"length_{field}",
            validation_type=ValidationType.LENGTH,
            field=field,
            message=message or f"Field '{field}' length is invalid"
        )
        self.min_length = min_length
        self.max_length = max_length
    
    def validate(self, value: Any, data: Dict) -> Optional[ValidationError]:
        """验证值"""
        if value is None:
            return None
        
        length = len(value)
        
        if self.min_length is not None and length < self.min_length:
            return ValidationError(
                field=self.field,
                message=f"Field '{self.field}' must be at least {self.min_length} characters",
                level=self.level,
                validation_type=self.validation_type,
                value=length,
                expected=f">= {self.min_length}"
            )
        
        if self.max_length is not None and length > self.max_length:
            return ValidationError(
                field=self.field,
                message=f"Field '{self.field}' must be at most {self.max_length} characters",
                level=self.level,
                validation_type=self.validation_type,
                value=length,
                expected=f"<= {self.max_length}"
            )
        
        return None


class RangeRule(ValidationRule):
    """范围验证规则"""
    
    def __init__(
        self,
        field: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        message: str = ""
    ):
        super().__init__(
            name=f"range_{field}",
            validation_type=ValidationType.RANGE,
            field=field,
            message=message or f"Field '{self.field}' value is out of range"
        )
        self.min_value = min_value
        self.max_value = max_value
    
    def validate(self, value: Any, data: Dict) -> Optional[ValidationError]:
        """验证值"""
        if value is None or not isinstance(value, (int, float)):
            return None
        
        if self.min_value is not None and value < self.min_value:
            return ValidationError(
                field=self.field,
                message=f"Field '{self.field}' must be at least {self.min_value}",
                level=self.level,
                validation_type=self.validation_type,
                value=value,
                expected=f">= {self.min_value}"
            )
        
        if self.max_value is not None and value > self.max_value:
            return ValidationError(
                field=self.field,
                message=f"Field '{self.field}' must be at most {self.max_value}",
                level=self.level,
                validation_type=self.validation_type,
                value=value,
                expected=f"<= {self.max_value}"
            )
        
        return None


class PatternRule(ValidationRule):
    """正则表达式验证规则"""
    
    def __init__(
        self,
        field: str,
        pattern: str,
        message: str = "",
        flags: int = 0
    ):
        super().__init__(
            name=f"pattern_{field}",
            validation_type=ValidationType.PATTERN,
            field=field,
            message=message or f"Field '{field}' does not match required pattern"
        )
        self.pattern = re.compile(pattern, flags)
    
    def validate(self, value: Any, data: Dict) -> Optional[ValidationError]:
        """验证值"""
        if value is None:
            return None
        
        if not isinstance(value, str):
            value = str(value)
        
        if not self.pattern.match(value):
            return ValidationError(
                field=self.field,
                message=self.message,
                level=self.level,
                validation_type=self.validation_type,
                value=value
            )
        
        return None


class EmailRule(ValidationRule):
    """邮箱验证规则"""
    
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    def __init__(self, field: str, message: str = ""):
        super().__init__(
            name=f"email_{field}",
            validation_type=ValidationType.PATTERN,
            field=field,
            message=message or f"Field '{field}' is not a valid email address"
        )
    
    def validate(self, value: Any, data: Dict) -> Optional[ValidationError]:
        """验证值"""
        if value is None:
            return None
        
        if not self.EMAIL_PATTERN.match(str(value)):
            return ValidationError(
                field=self.field,
                message=self.message,
                level=self.level,
                validation_type=self.validation_type,
                value=value
            )
        
        return None


class CustomRule(ValidationRule):
    """自定义验证规则"""
    
    def __init__(
        self,
        field: str,
        validator: Callable[[Any, Dict], bool],
        message: str = "",
        error_level: ValidationLevel = ValidationLevel.ERROR
    ):
        super().__init__(
            name=f"custom_{field}",
            validation_type=ValidationType.CUSTOM,
            field=field,
            message=message or f"Field '{field}' failed custom validation",
            level=error_level
        )
        self.validator = validator
    
    def validate(self, value: Any, data: Dict) -> Optional[ValidationError]:
        """验证值"""
        try:
            if not self.validator(value, data):
                return ValidationError(
                    field=self.field,
                    message=self.message,
                    level=self.level,
                    validation_type=self.validation_type,
                    value=value
                )
        except Exception as e:
            return ValidationError(
                field=self.field,
                message=f"Custom validation error: {str(e)}",
                level=ValidationLevel.ERROR,
                validation_type=self.validation_type,
                value=value
            )
        
        return None


class InputValidator:
    """输入验证器"""
    
    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode
        self._rules: Dict[str, List[ValidationRule]] = {}
        self._global_rules: List[ValidationRule] = []
    
    def add_rule(self, field: str, rule: ValidationRule):
        """添加验证规则"""
        if field not in self._rules:
            self._rules[field] = []
        self._rules[field].append(rule)
        logger.debug(f"Added rule '{rule.name}' for field '{field}'")
    
    def add_rules(self, field: str, rules: List[ValidationRule]):
        """批量添加验证规则"""
        for rule in rules:
            self.add_rule(field, rule)
    
    def add_global_rule(self, rule: ValidationRule):
        """添加全局验证规则"""
        self._global_rules.append(rule)
    
    def add_required(self, field: str, message: str = ""):
        """添加必填验证"""
        self.add_rule(field, RequiredRule(field, message))
    
    def add_type(self, field: str, expected_type: type, message: str = ""):
        """添加类型验证"""
        self.add_rule(field, TypeRule(field, expected_type, message))
    
    def add_length(
        self,
        field: str,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        message: str = ""
    ):
        """添加长度验证"""
        self.add_rule(field, LengthRule(field, min_length, max_length, message))
    
    def add_range(
        self,
        field: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        message: str = ""
    ):
        """添加范围验证"""
        self.add_rule(field, RangeRule(field, min_value, max_value, message))
    
    def add_pattern(self, field: str, pattern: str, message: str = ""):
        """添加正则验证"""
        self.add_rule(field, PatternRule(field, pattern, message))
    
    def add_email(self, field: str, message: str = ""):
        """添加邮箱验证"""
        self.add_rule(field, EmailRule(field, message))
    
    def add_custom(
        self,
        field: str,
        validator: Callable[[Any, Dict], bool],
        message: str = "",
        error_level: ValidationLevel = ValidationLevel.ERROR
    ):
        """添加自定义验证"""
        self.add_rule(field, CustomRule(field, validator, message, error_level))
    
    def validate(self, data: Dict) -> ValidationResult:
        """验证数据"""
        result = ValidationResult(valid=True, validated_data=data.copy())
        
        for rule in self._global_rules:
            error = rule.validate(data, data)
            if error:
                result.add_error(error)
                if self.strict_mode and error.level == ValidationLevel.CRITICAL:
                    break
        
        for field, rules in self._rules.items():
            value = data.get(field)
            
            for rule in rules:
                error = rule.validate(value, data)
                if error:
                    result.add_error(error)
                    if self.strict_mode and error.level == ValidationLevel.CRITICAL:
                        break
            
            if self.strict_mode and not result.valid:
                break
        
        return result
    
    async def validate_async(self, data: Dict) -> ValidationResult:
        """异步验证"""
        return self.validate(data)
    
    def clear_rules(self, field: Optional[str] = None):
        """清除规则"""
        if field:
            self._rules.pop(field, None)
        else:
            self._rules.clear()
            self._global_rules.clear()
    
    def get_rules(self, field: str) -> List[ValidationRule]:
        """获取字段的规则"""
        return self._rules.get(field, [])


class ValidatorFactory:
    """验证器工厂"""
    
    @staticmethod
    def create_prompt_validator() -> InputValidator:
        """创建提示词验证器"""
        validator = InputValidator()
        validator.add_required("prompt")
        validator.add_type("prompt", str)
        validator.add_length("prompt", min_length=1, max_length=100000)
        return validator
    
    @staticmethod
    def create_task_validator() -> InputValidator:
        """创建任务验证器"""
        validator = InputValidator()
        validator.add_required("task_id")
        validator.add_type("task_id", str)
        validator.add_pattern("task_id", r'^[a-zA-Z0-9_-]+$')
        validator.add_required("action")
        validator.add_type("action", str)
        return validator
    
    @staticmethod
    def create_config_validator() -> InputValidator:
        """创建配置验证器"""
        validator = InputValidator()
        validator.add_required("model")
        validator.add_type("model", str)
        validator.add_range("temperature", min_value=0.0, max_value=2.0)
        validator.add_range("max_tokens", min_value=1, max_value=100000)
        return validator
