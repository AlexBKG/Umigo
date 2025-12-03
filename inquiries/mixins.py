from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect


class StudentRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin to restrict access to students only.
    Used for actions that only students can perform (e.g., reporting listings).
    """
    def test_func(self):
        user = self.request.user
        if not user.is_active:
            return False
        try:
            return user.student_profile is not None
        except AttributeError:
            return False

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        return redirect('listings:listing_public_list')


class CanReportMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin to restrict access to users who can report (students and landlords).
    Used for general reporting functionality.
    """
    def test_func(self):
        user = self.request.user
        if not user.is_active:
            return False
        # Students and landlords can report
        try:
            return user.student_profile is not None
        except AttributeError:
            pass
        try:
            return user.landlord_profile is not None
        except AttributeError:
            pass
        return False

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        return redirect('listings:listing_public_list')
