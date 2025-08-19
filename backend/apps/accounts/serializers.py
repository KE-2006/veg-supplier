from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, CustomerProfile

class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone', 
                 'address', 'password', 'password_confirm', 'user_type')
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        
        # Create customer profile if user is customer
        if user.user_type == 'customer':
            CustomerProfile.objects.create(user=user)
        
        return user

class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    username = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include username and password')
        
        return attrs

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile"""
    customer_profile = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 
                 'phone', 'address', 'user_type', 'customer_profile')
        read_only_fields = ('id', 'username', 'user_type')
    
    def get_customer_profile(self, obj):
        if hasattr(obj, 'customer_profile'):
            return {
                'loyalty_points': obj.customer_profile.loyalty_points,
                'total_orders': obj.customer_profile.total_orders,
                'total_spent': float(obj.customer_profile.total_spent),
                'preferred_delivery_time': obj.customer_profile.preferred_delivery_time,
            }
        return None
