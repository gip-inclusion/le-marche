from django.test import SimpleTestCase

from lemarche.utils.sanitize import sanitize_html


class SanitizeHtmlTest(SimpleTestCase):
    def test_empty_values_return_empty_string(self):
        self.assertEqual(sanitize_html(""), "")
        self.assertEqual(sanitize_html(None), "")

    def test_removes_script_tag(self):
        self.assertNotIn("<script", sanitize_html("<p>hello</p><script>alert('xss')</script>"))

    def test_removes_event_handler_attribute(self):
        cleaned = sanitize_html('<img src=x onerror="alert(1)">')
        self.assertNotIn("onerror", cleaned)
        self.assertNotIn("<img", cleaned)

    def test_removes_iframe(self):
        self.assertNotIn("<iframe", sanitize_html('<iframe src="https://evil.example"></iframe>'))

    def test_drops_javascript_url_scheme(self):
        cleaned = sanitize_html('<a href="javascript:alert(1)">x</a>')
        self.assertNotIn("javascript:", cleaned)

    def test_preserves_formatting_tags(self):
        html = "<p><strong>gras</strong> <em>italique</em></p><ul><li>un</li></ul>"
        self.assertEqual(sanitize_html(html), html)

    def test_preserves_structural_tags(self):
        # balises structurelles plus riches (contenu partenaire APProch)
        html = (
            '<div><h1>Titre</h1><table><thead><tr><th scope="col" colspan="2">H</th></tr></thead>'
            "<tbody><tr><td>a</td><td>b</td></tr></tbody></table></div>"
        )
        self.assertEqual(sanitize_html(html), html)

    def test_strips_style_attribute(self):
        # le style reste interdit (clickjacking / exfiltration CSS)
        self.assertNotIn("style", sanitize_html('<div style="position:fixed">x</div>'))

    def test_preserves_links_and_adds_noopener_rel(self):
        html = '<a href="https://example.com" target="_blank">lien</a>'
        cleaned = sanitize_html(html)
        self.assertIn('href="https://example.com"', cleaned)
        self.assertIn('target="_blank"', cleaned)
        self.assertIn("lien", cleaned)
        # nh3 ajoute rel="noopener noreferrer" sur les liens
        self.assertIn("noopener", cleaned)
