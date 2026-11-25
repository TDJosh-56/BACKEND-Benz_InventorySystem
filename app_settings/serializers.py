from rest_framework import serializers

from .models import Setting


def validate_four_digit_pin(value: str) -> str:
    # limits passcode to 4 digits
    if not value.isdigit() or len(value) != 4:
        raise serializers.ValidationError("Passcode must be exactly 4 numeric digits.")
    return value


class SettingSerializer(serializers.ModelSerializer):
    autoArchiveOldRecipes = serializers.BooleanField(source='autoarchiveoldrecipe')

    class Meta:
        model = Setting
        fields = ['autoArchiveOldRecipes', 'updated_at']
        read_only_fields = ['updated_at']

class PasscodeSerializer(serializers.Serializer):
    passcode = serializers.CharField(
        min_length = 4,
        max_length = 4,
        trim_whitespace = True,
        write_only = True,
        validators = [validate_four_digit_pin],
    )

class RecoveryCodeSerializer(serializers.Serializer):
    recovery_code = serializers.CharField(
        max_length = 64,
        trim_whitespace = True,
        write_only = True,
    )

    def validate_recovery_code(self, value: str) -> str:
        return value.strip().upper()


class ResetPasscodeSerializer(serializers.Serializer):
    recovery_code = serializers.CharField(
        required=True,
        allow_blank=False,
        max_length=64,
        trim_whitespace=True,
        write_only=True,
    )
    new_passcode = serializers.CharField(
        min_length=4,
        max_length=4,
        trim_whitespace=True,
        write_only=True,
        validators=[validate_four_digit_pin],
    )
    confirm_passcode = serializers.CharField(
        min_length=4,
        max_length=4,
        trim_whitespace=True,
        write_only=True,
        validators=[validate_four_digit_pin],
    )

    def validate_recovery_code(self, value: str) -> str:
        return value.strip().upper()

    def validate(self, attrs):
        if attrs["new_passcode"] != attrs["confirm_passcode"]:
            raise serializers.ValidationError(
                {"confirm_passcode": "New passcode and confirmation do not match."}
            )
        return attrs

class ChangePasscodeSerializer(serializers.Serializer):
    current_passcode = serializers.CharField(
        min_length = 4,
        max_length = 4,
        trim_whitespace = True,
        write_only = True,
        validators = [validate_four_digit_pin]
    )
    new_passcode = serializers.CharField(
        min_length = 4,
        max_length = 4,
        trim_whitespace = True,
        write_only = True,
        validators = [validate_four_digit_pin]
    )
    confirm_passcode = serializers.CharField(
        min_length = 4,
        max_length = 4,
        trim_whitespace = True,
        write_only = True,
        validators = [validate_four_digit_pin]
    )

    def validate(self, attrs):
        if attrs["new_passcode"] != attrs["confirm_passcode"]:
            raise serializers.ValidationError(
                {"confirm_passcode": "New passcode and confirmation do not match."}
            )
    def validate(self, attrs):
        if attrs["current_passcode"] != attrs["new_passcode"]:
            raise serializers.ValidationError(
                {"confirm_passcode": "New passcode must be different from the current passcode."}
            )
        return attrs