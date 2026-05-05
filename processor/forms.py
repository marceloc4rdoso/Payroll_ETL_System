from __future__ import annotations

from django import forms
from django.forms import formset_factory

from people.models import Empresa
from processor.models import BillingLine, BillingOrder, ServiceProduct, SourceSystem, Upload
from processor.models import BillingClosure


class UploadForm(forms.Form):
    """
    Form simples para upload de TXT + seleção de empresa/layout.

    A seleção de Empresa é parte do fluxo descrito na spec.md.
    """

    empresa = forms.ModelChoiceField(queryset=Empresa.objects.filter(is_active=True))
    arquivo = forms.FileField()

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if not user or getattr(user, "is_staff", False) or getattr(user, "is_superuser", False):
            self.fields["empresa"].queryset = Empresa.objects.filter(is_active=True)
            return

        vinculo = getattr(user, "empresa_vinculo", None)
        empresa = getattr(vinculo, "empresa", None) if getattr(vinculo, "is_active", False) else None
        if not empresa:
            contato = getattr(user, "contato", None)
            empresa = getattr(contato, "empresa", None) if getattr(contato, "is_active", False) else None
        if empresa and getattr(empresa, "is_active", False):
            self.fields["empresa"].queryset = Empresa.objects.filter(pk=empresa.pk, is_active=True)
            self.fields["empresa"].initial = empresa.pk
            self.fields["empresa"].widget = forms.HiddenInput()
        else:
            self.fields["empresa"].queryset = Empresa.objects.none()

    def clean_arquivo(self):
        f = self.cleaned_data["arquivo"]
        if not f.name.lower().endswith(".txt"):
            raise forms.ValidationError("Envie um arquivo .txt.")
        return f

    def clean_empresa(self):
        empresa = self.cleaned_data.get("empresa")
        if not empresa:
            raise forms.ValidationError("Seu usuário não está vinculado a uma empresa ativa. Contate o administrador.")
        return empresa


class SourceSystemForm(forms.ModelForm):
    class Meta:
        model = SourceSystem
        fields = ["code", "name", "is_active", "sample_file"]

    def clean_code(self):
        code = (self.cleaned_data["code"] or "").strip().upper()
        return code

    def clean_sample_file(self):
        f = self.cleaned_data.get("sample_file")
        if not f:
            return f
        if not f.name.lower().endswith(".txt"):
            raise forms.ValidationError("Envie um arquivo .txt como modelo.")
        return f


class LayoutMetaForm(forms.Form):
    record_marker_regex = forms.CharField(
        label="Marcador de início do holerite (Regex)",
        required=True,
        initial=r"^\s*1",
        help_text="Regex para identificar a linha que inicia cada holerite/registro no arquivo.",
    )
    detail_start_line_offset = forms.IntegerField(
        label="Detail: linha inicial (offset)",
        required=True,
        initial=1,
        min_value=0,
        help_text="Linha inicial do detail a partir do marcador (1 = primeira linha do holerite/marcador).",
    )
    detail_max_lines = forms.IntegerField(
        label="Detail: máximo de linhas",
        required=True,
        initial=0,
        min_value=0,
        help_text="Quantidade máxima de linhas reservadas para detalhes (preenche com linhas em branco se faltar).",
    )
    detail_pad_to_max = forms.BooleanField(
        label="Detail: completar até o máximo",
        required=False,
        initial=False,
    )
    detail_index_format = forms.ChoiceField(
        label="Detail: padrão de nome das colunas",
        required=True,
        choices=[
            ("{base}{i}", "detail_cod1 / detail_description1 (sem _ e sem zero à esquerda)"),
            ("{base}_{i:02d}", "detail_cod_01 / detail_description_01 (com _01)"),
        ],
        initial="{base}{i}",
    )
    bottom_marker_regex = forms.CharField(
        label="Marcador do Bottom (Regex)",
        required=False,
        initial="",
        help_text="Opcional. Se informado, a primeira linha que casar com a regex será considerada início do bottom (não entra no detail).",
    )
    bottom_start_line_offset = forms.IntegerField(
        label="Bottom: linha inicial (offset)",
        required=False,
        min_value=0,
        help_text="Opcional. Se informado, define a linha inicial do bottom (1 = primeira linha do holerite/marcador).",
    )
    bottom_base_line = forms.ChoiceField(
        label="Bottom: base do offset",
        required=True,
        choices=[
            ("record", "Offset relativo ao início do holerite"),
            ("bottom", "Offset relativo ao início do Bottom"),
        ],
        initial="bottom",
    )


class LayoutFieldForm(forms.Form):
    name = forms.CharField(label="Campo", required=False)
    start = forms.IntegerField(label="Start (coluna)", required=False, min_value=0)
    end = forms.IntegerField(label="End (coluna)", required=False, min_value=0)
    line_offset = forms.IntegerField(label="Linha (1 = primeira)", required=False, min_value=0)
    enabled = forms.BooleanField(label="Ativo", required=False, initial=True)

    def clean(self):
        cleaned = super().clean()
        name = (cleaned.get("name") or "").strip()
        enabled = bool(cleaned.get("enabled", False))
        start = cleaned.get("start")
        end = cleaned.get("end")
        if enabled and name:
            if start is None or end is None:
                raise forms.ValidationError("Start e End são obrigatórios para campos ativos.")
            if end < start:
                raise forms.ValidationError("End deve ser maior ou igual ao Start.")
        return cleaned


LayoutFieldFormSet = formset_factory(LayoutFieldForm, extra=30, can_delete=False)


class ServiceProductForm(forms.ModelForm):
    class Meta:
        model = ServiceProduct
        fields = ["code", "name", "product_type", "unit_price", "is_active", "is_default_for_uploads"]

    def clean_code(self):
        return (self.cleaned_data.get("code") or "").strip().upper()


class BillingOrderForm(forms.ModelForm):
    class Meta:
        model = BillingOrder
        fields = ["empresa", "launch_date", "status"]


class BillingLineForm(forms.ModelForm):
    class Meta:
        model = BillingLine
        fields = ["product", "upload", "manual_label", "quantity"]

    def __init__(self, *args, empresa=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["product"].queryset = ServiceProduct.objects.filter(is_active=True).order_by("name")
        if empresa is not None:
            self.fields["upload"].queryset = Upload.objects.filter(empresa=empresa).order_by("-created_at")[:500]
        else:
            self.fields["upload"].queryset = Upload.objects.none()
        self.fields["upload"].help_text = "Opcional. Se selecionar um Upload, pode deixar a quantidade vazia para usar os registros calculados."
        self.fields["manual_label"].help_text = "Opcional. Use quando o CSV foi gerado fora do sistema."
        self.fields["quantity"].help_text = "Obrigatório. Se você selecionou um Upload com registros calculados, pode deixar vazio para preencher automaticamente."

    def clean(self):
        cleaned = super().clean()
        product = cleaned.get("product")
        upload = cleaned.get("upload")
        manual_label = (cleaned.get("manual_label") or "").strip()
        quantity = cleaned.get("quantity")

        if not product:
            return cleaned

        if upload and manual_label:
            raise forms.ValidationError("Use Upload ou Descrição manual, não ambos.")

        if upload and quantity is None:
            cleaned["quantity"] = int(upload.row_count or 0)

        if not upload and quantity is None:
            if getattr(product, "product_type", None) == ServiceProduct.ProductType.FIXED:
                cleaned["quantity"] = 1

        if cleaned.get("quantity") is None:
            raise forms.ValidationError("Informe a quantidade.")

        return cleaned


class BillingClosureForm(forms.ModelForm):
    class Meta:
        model = BillingClosure
        fields = ["empresa", "year", "month"]

    def clean_month(self):
        m = int(self.cleaned_data["month"])
        if m < 1 or m > 12:
            raise forms.ValidationError("Mês deve ser entre 1 e 12.")
        return m
