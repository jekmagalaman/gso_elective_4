from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()


class UserForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Enter password"}),
        label="Password"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Confirm password"}),
        label="Confirm Password"
    )

    class Meta:
        model = User
        fields = [
            "role",
            "unit",
            "username",
            "first_name",
            "last_name",
            "email",
            "department",
            "account_status",
            "password",
        ]

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user


class UserEditForm(forms.ModelForm):
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'autocomplete': 'off'}),
        required=False,
        label="Old Password",
        help_text="Optional: Fill only if you want to change the password."
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Enter new password"}),
        required=False,
        label="New Password"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Confirm new password"}),
        required=False,
        label="Confirm New Password"
    )

    class Meta:
        model = User
        fields = ["username", "role", "unit", "first_name", "last_name", "email", "department", "account_status"]

    def clean(self):
        cleaned_data = super().clean()
        old_pass = cleaned_data.get("old_password")
        new_pass = cleaned_data.get("new_password")
        confirm_pass = cleaned_data.get("confirm_password")

        # Only validate if user wants to change password
        if new_pass or confirm_pass:
            if new_pass != confirm_pass:
                raise forms.ValidationError("New password and confirmation do not match.")

            if old_pass:
                if not self.instance.check_password(old_pass):
                    raise forms.ValidationError("Old password is incorrect.")
            else:
                raise forms.ValidationError("Please enter your old password to set a new password.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        new_pass = self.cleaned_data.get("new_password")
        if new_pass:
            user.set_password(new_pass)
        if commit:
            user.save()
        return user


class RequestorProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["department", "email"]
