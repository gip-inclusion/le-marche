from rest_framework import serializers


class UserInboundParsingSerializer(serializers.DictField):
    Name = serializers.CharField()
    Address = serializers.EmailField()


class EmailItemSerializer(serializers.Serializer):
    Uuid = serializers.ListField(child=serializers.UUIDField())
    MessageId = serializers.CharField()
    InReplyTo = serializers.CharField(allow_null=True)
    From = UserInboundParsingSerializer()
    To = serializers.ListField(child=UserInboundParsingSerializer())
    Cc = serializers.ListField(child=UserInboundParsingSerializer(), allow_empty=True)
    ReplyTo = serializers.CharField(allow_null=True)
    SentAtDate = serializers.CharField()
    Subject = serializers.CharField()
    RawHtmlBody = serializers.CharField()
    RawTextBody = serializers.CharField()
    ExtractedMarkdownMessage = serializers.CharField()
    ExtractedMarkdownSignature = serializers.CharField()
    SpamScore = serializers.FloatField()
    Attachments = serializers.ListField(child=serializers.DictField())
    Headers = serializers.DictField()


class EmailsSerializer(serializers.Serializer):
    items = serializers.ListField(child=EmailItemSerializer())
