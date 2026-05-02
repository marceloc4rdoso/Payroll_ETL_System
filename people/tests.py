from django.contrib.auth import get_user_model
from django.forms import HiddenInput
from django.test import TestCase
from django.test import Client
from django.urls import reverse

from people.forms import ContatoForm
from people.models import Contato
from people.models import Empresa, UserEmpresaVinculo
from processor.forms import UploadForm


class UserEmpresaVinculoAccessTests(TestCase):
    def test_non_staff_upload_form_auto_selects_linked_company(self):
        empresa = Empresa.objects.create(name="Empresa A", cnpj="12345678000199", layout_type="GENESIS")
        user = get_user_model().objects.create_user(username="u1", password="pw")
        UserEmpresaVinculo.objects.create(user=user, empresa=empresa, is_active=True)

        form = UploadForm(user=user)
        self.assertEqual(list(form.fields["empresa"].queryset), [empresa])
        self.assertIsInstance(form.fields["empresa"].widget, HiddenInput)

    def test_non_staff_without_linked_company_gets_validation_error(self):
        user = get_user_model().objects.create_user(username="u2", password="pw")
        form = UploadForm(data={"empresa": "", "arquivo": ""}, user=user)
        self.assertFalse(form.is_valid())
        self.assertIn("empresa", form.errors)

    def test_non_staff_cannot_access_systems_or_people_crud(self):
        user = get_user_model().objects.create_user(username="u3", password="pw")
        self.client.force_login(user)

        resp_systems = self.client.get(reverse("processor:system_list"))
        self.assertEqual(resp_systems.status_code, 403)

        resp_empresas = self.client.get(reverse("people:empresa_list"))
        self.assertEqual(resp_empresas.status_code, 403)

    def test_creating_contact_creates_user_and_vinculo(self):
        empresa = Empresa.objects.create(name="Valdequimica", cnpj="12345678000111", layout_type="GENESIS")
        form = ContatoForm(
            data={
                "empresa": empresa.pk,
                "name": "Ana",
                "email": "ana@valdequimica.com.br",
                "phone": "",
                "role": "",
                "is_active": True,
            }
        )
        self.assertTrue(form.is_valid(), form.errors.as_json())
        contato = form.save()
        self.assertIsNotNone(contato.user_id)
        self.assertTrue(UserEmpresaVinculo.objects.filter(user=contato.user, empresa=empresa, is_active=True).exists())

    def test_contact_on_maintainer_company_becomes_admin(self):
        empresa = Empresa.objects.create(
            name="Capybird Maker Labs",
            cnpj="12345678000222",
            layout_type="GENESIS",
            is_maintainer=True,
        )
        form = ContatoForm(
            data={
                "empresa": empresa.pk,
                "name": "Marcelo",
                "email": "marcelo@capybird.com.br",
                "phone": "",
                "role": "",
                "is_active": True,
            }
        )
        self.assertTrue(form.is_valid(), form.errors.as_json())
        contato = form.save()
        self.assertTrue(contato.user.is_staff)
        self.assertTrue(contato.user.is_superuser)


class CsrfLogoutTests(TestCase):
    def test_logout_post_with_csrf_redirects(self):
        user = get_user_model().objects.create_user(username="u_logout", password="pw")
        client = Client(enforce_csrf_checks=True)
        client.login(username="u_logout", password="pw")

        resp_get = client.get(reverse("processor:dashboard"))
        csrf_cookie = resp_get.cookies.get("csrftoken")
        self.assertIsNotNone(csrf_cookie)

        resp_post = client.post(reverse("logout"), data={}, HTTP_X_CSRFTOKEN=csrf_cookie.value)
        self.assertIn(resp_post.status_code, (200, 302, 303))
