from rest_framework import serializers


class DummySerializer(serializers.Serializer):
    pass


class DetailSerializer(serializers.Serializer):
    detail = serializers.CharField()
