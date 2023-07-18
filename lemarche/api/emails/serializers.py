from rest_framework import serializers


class EmailItemSerializer(serializers.Serializer):
    Uuid = serializers.ListField(child=serializers.UUIDField())
    MessageId = serializers.CharField()
    InReplyTo = serializers.CharField(allow_null=True)
    From = serializers.DictField(child=serializers.CharField())
    To = serializers.ListField(child=serializers.DictField(child=serializers.CharField()))
    Cc = serializers.ListField(child=serializers.DictField(child=serializers.CharField()), allow_empty=True)
    ReplyTo = serializers.CharField(allow_null=True)
    SentAtDate = serializers.CharField()
    Subject = serializers.CharField()
    RawHtmlBody = serializers.CharField()
    RawTextBody = serializers.CharField()
    ExtractedMarkdownMessage = serializers.CharField()
    ExtractedMarkdownSignature = serializers.CharField()
    SpamScore = serializers.FloatField()
    Attachments = serializers.ListField(child=serializers.DictField(child=serializers.CharField()))
    Headers = serializers.DictField(child=serializers.CharField())


class EmailsSerializer(serializers.Serializer):
    items = EmailItemSerializer(many=True)
