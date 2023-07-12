from rest_framework import serializers

from parties.models import Party, PartyDescription, PartyEmblem


class PartyEmblemSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = PartyEmblem
        ref_name = None  # Tells swagger that this is always embedded
        fields = (
            "image",
            "description",
            "date_approved",
            "ec_emblem_id",
            "default",
            "active",
        )
        swagger_schema_fields = {"description": model.__doc__}


class DefaultPartyEmblemSerializer(PartyEmblemSerializer):
    """
    Simply used to change the help text aways from the PartyEmblem docstring,
    as it's helpful to explain why this property exists.

    """

    class Meta(PartyEmblemSerializer.Meta):
        swagger_schema_fields = {"description": Party.default_emblem.__doc__}


class PartyDescriptionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = PartyDescription
        ref_name = None  # Tells swagger that this is always embedded
        fields = ("description", "date_description_approved", "active")
        swagger_schema_fields = {"description": model.__doc__}


class PartySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Party
        fields = (
            "ec_id",
            "url",
            "name",
            "alternative_name",
            "register",
            "nations",
            "status",
            "date_registered",
            "date_deregistered",
            "default_emblem",
            "emblems",
            "descriptions",
            "legacy_slug",
            "created",
            "last_updated",
        )
        swagger_schema_fields = {"description": model.__doc__}

    url = serializers.HyperlinkedIdentityField(
        view_name="party-detail", lookup_field="ec_id", lookup_url_kwarg="ec_id"
    )
    default_emblem = DefaultPartyEmblemSerializer(read_only=True)
    emblems = PartyEmblemSerializer(many=True, read_only=True)
    descriptions = PartyDescriptionSerializer(many=True, read_only=True)
    last_updated = serializers.DateTimeField(source="modified")


class PartyRegisterSerializer(serializers.Serializer):
    class Meta:
        ref_name = None  # Tells swagger that this is always embedded

    register = serializers.CharField(max_length=2)


class MinimalPartySerializer(PartySerializer):
    class Meta:
        model = Party
        ref_name = None  # Tells swagger that this is always embedded
        fields = ("url", "ec_id", "name", "legacy_slug", "created", "modified")
        swagger_schema_fields = {"description": Party.__doc__}


class CSVPartySerializer(PartySerializer):
    class Meta:
        model = Party
        ref_name = None  # Tells swagger that this is always embedded
        fields = ("name", "ec_id", "current_candidates")
        swagger_schema_fields = {"description": Party.__doc__}

    ec_id = serializers.SerializerMethodField()

    def get_ec_id(self, party):
        return party.ec_id.replace("PP", "")
