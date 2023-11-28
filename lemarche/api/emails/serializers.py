from rest_framework import serializers


class UserInboundParsingSerializer(serializers.DictField):
    Name = serializers.CharField(required=False, allow_null=True)
    Address = serializers.EmailField()


class EmailItemSerializer(serializers.Serializer):
    """Email ItemSerializer for data comes from Brevo"""

    Uuid = serializers.ListField(child=serializers.UUIDField())
    MessageId = serializers.CharField()
    InReplyTo = serializers.CharField(required=False, allow_null=True)
    From = UserInboundParsingSerializer()
    To = serializers.ListField(child=UserInboundParsingSerializer())
    Cc = serializers.ListField(child=UserInboundParsingSerializer(), required=False)
    ReplyTo = serializers.CharField(required=False, allow_null=True)
    SentAtDate = serializers.CharField()
    Subject = serializers.CharField(required=False, allow_null=True)
    RawHtmlBody = serializers.CharField(required=False, allow_null=True)
    RawTextBody = serializers.CharField(required=False, allow_null=True)
    ExtractedMarkdownMessage = serializers.CharField(required=False, allow_null=True)
    ExtractedMarkdownSignature = serializers.CharField(required=False, allow_null=True)
    SpamScore = serializers.FloatField()
    Attachments = serializers.ListField(child=serializers.DictField(), required=False)
    Headers = serializers.DictField()


class EmailsSerializer(serializers.Serializer):
    items = serializers.ListField(child=EmailItemSerializer())
