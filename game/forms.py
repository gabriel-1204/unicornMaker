from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User


# ============================================================
# 회원가입 폼 (유동주 담당)
# ============================================================
class SignupForm(UserCreationForm):
    """
    회원가입 폼
    - UserCreationForm 상속 (username, password1, password2 자동 포함)
    - 추가 필드: nickname, img_profile
    """
    nickname = forms.CharField(
        max_length=20,
        required=True,
        label='닉네임',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '닉네임을 입력하세요'
        })
    )
    img_profile = forms.ImageField(
        required=False,
        label='프로필 이미지 (선택)',
        widget=forms.FileInput(attrs={
            'class': 'form-control'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'nickname', 'password1', 'password2', 'img_profile']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '아이디를 입력하세요'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 비밀번호 필드 스타일 적용
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': '비밀번호를 입력하세요'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': '비밀번호를 다시 입력하세요'
        })

    # TODO (유동주): 닉네임 중복 검사 추가
    # def clean_nickname(self):
    #     nickname = self.cleaned_data.get('nickname')
    #     if User.objects.filter(nickname=nickname).exists():
    #         raise forms.ValidationError('이미 사용 중인 닉네임입니다.')
    #     return nickname


# ============================================================
# 로그인 폼 (유동주 담당)
# ============================================================
class LoginForm(AuthenticationForm):
    """
    로그인 폼
    - AuthenticationForm 상속 (username, password 자동 포함)
    """
    username = forms.CharField(
        label='아이디',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '아이디를 입력하세요'
        })
    )
    password = forms.CharField(
        label='비밀번호',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '비밀번호를 입력하세요'
        })
    )

    # TODO (유동주): 로그인 실패 메시지 커스터마이징
    # error_messages = {
    #     'invalid_login': '아이디 또는 비밀번호가 올바르지 않습니다.',
    # }
