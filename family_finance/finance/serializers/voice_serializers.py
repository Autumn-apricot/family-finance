from rest_framework import serializers


class VoiceParseSerializer(serializers.Serializer):
    text = serializers.CharField(min_length=1, max_length=500)
    reference_date = serializers.DateField(required=False, allow_null=True)


class VoiceConfirmSerializer(serializers.Serializer):
    expense_id = serializers.IntegerField(min_value=1)
