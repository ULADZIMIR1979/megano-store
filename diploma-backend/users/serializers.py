from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['fullName', 'email', 'phone', 'avatar']
        read_only_fields = ['avatar']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Обработка аватара
        if instance.avatar:
            request = self.context.get('request')
            if request:
                representation['avatar'] = {
                    'src': request.build_absolute_uri(instance.avatar.url),
                    'alt': 'Avatar'
                }
            else:
                representation['avatar'] = {
                    'src': instance.avatar.url,
                    'alt': 'Avatar'
                }
        else:
            representation['avatar'] = {
                'src': '/static/frontend/assets/img/user_icon.png',
                'alt': 'Avatar'
            }
        return representation


# class UserRegistrationSerializer(serializers.ModelSerializer):
#     password = serializers.CharField(write_only=True, validators=[validate_password])
#     password_confirm = serializers.CharField(write_only=True)
#
#     class Meta:
#         model = User
#         fields = ['fullName', 'email', 'phone', 'password', 'password_confirm']
#
#     def validate(self, attrs):
#         if attrs['password'] != attrs['password_confirm']:
#             raise serializers.ValidationError({"password_confirm": "Пароли не совпадают"})
#         return attrs
#
#     def create(self, validated_data):
#         validated_data.pop('password_confirm')
#         user = User.objects.create_user(
#             username=validated_data['email'],  # используем email как username
#             email=validated_data['email'],
#             fullName=validated_data.get('fullName', ''),
#             phone=validated_data.get('phone', ''),
#             password=validated_data['password']
#         )
#         return user


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password], required=True)
    password_confirm = serializers.CharField(write_only=True, required=False)  # Сделать необязательным
    username = serializers.CharField(write_only=True, required=True)
    name = serializers.CharField(write_only=True, required=False, allow_blank=True, default='')

    class Meta:
        model = User
        fields = ['name', 'username', 'password', 'password_confirm']

    def validate(self, attrs):
        # Используем username как email
        attrs['email'] = attrs['username']

        # Проверяем уникальность username/email
        if User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError({"username": "Пользователь с таким именем уже существует"})

        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"username": "Пользователь с таким email уже существует"})

        return attrs

    def create(self, validated_data):
        # Извлекаем дополнительные поля
        name = validated_data.pop('name', '')
        username = validated_data.pop('username')
        email = validated_data.pop('email')
        password = validated_data.pop('password')
        validated_data.pop('password_confirm', None)

        user = User.objects.create_user(
            username=username,
            email=email,
            fullName=name,
            phone='',  # Пустое по умолчанию
            password=password
        )
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['fullName', 'email', 'phone']

    def validate_email(self, value):
        # Проверка уникальности email (исключая текущего пользователя)
        user = self.context['request'].user
        if User.objects.filter(email=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("Этот email уже используется.")
        return value

    def validate_phone(self, value):
        # Проверка уникальности телефона (исключая текущего пользователя)
        user = self.context['request'].user
        if User.objects.filter(phone=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("Этот телефон уже используется.")
        return value


class UserPasswordSerializer(serializers.Serializer):
    currentPassword = serializers.CharField(write_only=True)
    newPassword = serializers.CharField(write_only=True)

    def validate_newPassword(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        user = self.context['request'].user
        if not user.check_password(attrs['currentPassword']):
            raise serializers.ValidationError({'currentPassword': 'Неверный текущий пароль'})
        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['newPassword'])
        user.save()
        return user