from django.test import TestCase
from django.urls import reverse


EMAIL_JSON = {
    "items": [
        {
            "Uuid": ["1a825d56-029b-4a41-b8e4-61670463431b"],
            "MessageId": "<CAN0zNmMsj_xOx8hCREv3rbovcYE3m5rZh8eRe+QSKC0yff_W6A@mail.gmail.com>",
            "InReplyTo": "<e6df8cf2-cfb2-2cb6-320f-d9cba05a3001@clubble.me>",
            "From": {"Name": "Antoine Lefeuvre", "Address": "antoine@mailclark.ai"},
            "To": [{"Name": "Terry Estill", "Address": "test@clubble.me"}],
            "Cc": [],
            "ReplyTo": "madjid@test.com",
            "SentAtDate": "Tue, 1 Sep 2020 09:53:21 +0200",
            "Subject": "Re: Summer brochure 2021",
            "RawHtmlBody": '<div dir="ltr">Hi Terry,<br>Nice to hear from you, I hope you&#39;re well.<br>Sure, our summer brochure is already out \ud83d\ude0e! I&#39;ve attached it <b>together with our winter brochure\u00a0<\/b>\u26c4.<br><br>I&#39;ve heard you&#39;re a massive fan of <a href="https:\/\/en.wikipedia.org\/wiki\/Rubber_duck_debugging">rubber ducks<\/a>, so I wanted to share with you this picture I took this summer. <i>Amazing, eh?<\/i><div><div><img src="cid:ii_kejngtlh0" alt="duck1.png" width="294" height="196" style="margin-right: 0px;"><br><\/div><br>Any questions (about the brochures, not the ducks \ud83d\ude1c), I&#39;d\u00a0be happy to help.<br><br>Speak soon,\u00a0\u00a0<br clear="all"><div><div dir="ltr" class="gmail_signature" data-smartmail="gmail_signature"><div dir="ltr"><div><div dir="ltr"><div><div dir="ltr"><b>Antoine Lefeuvre<\/b><br>Co-founder &amp; Product Manager at <a href="https:\/\/mailclark.ai" target="_blank">MailClark<\/a><br><a href="mailto:antoine@mailclark.ai" target="_blank">antoine@mailclark.ai<\/a><br><a href="https:\/\/twitter.com\/jiraisurfer" target="_blank">Twitter<\/a> <a href="https:\/\/www.linkedin.com\/in\/lefeuvre" target="_blank">LinkedIn<\/a><br><i>Sent with MailClark<\/i><br><\/div><\/div><\/div><\/div><\/div><\/div><\/div><br><\/div><\/div><br><div class="gmail_quote"><div dir="ltr" class="gmail_attr">On Tue, 1 Sep 2020 at 09:43, Terry Estill &lt;<a href="mailto:test@clubble.me">test@clubble.me<\/a>&gt; wrote:<br><\/div><blockquote class="gmail_quote" style="margin:0px 0px 0px 0.8ex;border-left:1px solid rgb(204,204,204);padding-left:1ex">\n  \n    \n  \n  <div bgcolor="#FFFFFF">\n    <p>Hi there, I hope things with you are good.<br>\n      <br>\n      I was wondering whether your brochure for the summer next year was\n      already available. I&#39;m willing to start planning asap.<br>\n      <br>\n      Best,<br>\n    <\/p>\n    <div>-- <br>\n      <strong>Terry Estill<\/strong>\u2014Cofounder &amp; CEO<br>\n      <em>The Wheat Assembly - Le Club Bl\u00e9<\/em><br>\n      <a href="mailto:test@clubble.me" target="_blank">test@clubble.me<\/a><br>\n      <a href="http:\/\/www.clubble.me" target="_blank">www.clubble.me<\/a><\/div>\n  <\/div>\n\n<\/blockquote><\/div>\n',
            "RawTextBody": "Hi Terry,\nNice to hear from you, I hope you're well.\nSure, our summer brochure is already out \ud83d\ude0e! I've attached it *together\nwith our winter brochure *\u26c4.\n\nI've heard you're a massive fan of rubber ducks\n<https:\/\/en.wikipedia.org\/wiki\/Rubber_duck_debugging>, so I wanted to share\nwith you this picture I took this summer. *Amazing, eh?*\n[image: duck1.png]\n\nAny questions (about the brochures, not the ducks \ud83d\ude1c), I'd be happy to help.\n\nSpeak soon,\n*Antoine Lefeuvre*\nCo-founder & Product Manager at MailClark <https:\/\/mailclark.ai>\nantoine@mailclark.ai\nTwitter <https:\/\/twitter.com\/jiraisurfer> LinkedIn\n<https:\/\/www.linkedin.com\/in\/lefeuvre>\n*Sent with MailClark*\n\n\nOn Tue, 1 Sep 2020 at 09:43, Terry Estill <test@clubble.me> wrote:\n\n> Hi there, I hope things with you are good.\n>\n> I was wondering whether your brochure for the summer next year was already\n> available. I'm willing to start planning asap.\n>\n> Best,\n> --\n> *Terry Estill*\u2014Cofounder & CEO\n> *The Wheat Assembly - Le Club Bl\u00e9*\n> test@clubble.me\n> www.clubble.me\n>\n",
            "ExtractedMarkdownMessage": "Hi Terry,  \nNice to hear from you, I hope you're well.  \nSure, our summer brochure is already out \ud83d\ude0e! I've attached it **together with our winter brochure**\u00a0\u26c4.  \n\nI've heard you're a massive fan of [rubber ducks](https:\/\/en.wikipedia.org\/wiki\/Rubber_duck_debugging), so I wanted to share with you this picture I took this summer. *Amazing, eh?*  \n\n[duck1.png](ii_kejngtlh0)  \n\nAny questions (about the brochures, not the ducks \ud83d\ude1c), I'd\u00a0be happy to help.  \n\nSpeak soon,\u00a0\u00a0  \n",
            "ExtractedMarkdownSignature": "**Antoine Lefeuvre**  \nCo-founder &amp; Product Manager at [MailClark](https:\/\/mailclark.ai)  \n[antoine@mailclark.ai](mailto:antoine@mailclark.ai)  \n[Twitter](https:\/\/twitter.com\/jiraisurfer) [LinkedIn](https:\/\/www.linkedin.com\/in\/lefeuvre)  \n*Sent with MailClark*",
            "SpamScore": 3.3,
            "Attachments": [
                {
                    "Name": "duck1.png",
                    "ContentType": "image\/png",
                    "ContentLength": 330518,
                    "ContentID": "ii_kejngtlh0",
                    "DownloadToken": "abc",
                },
                {
                    "Name": "summer2021.pdf",
                    "ContentType": "application\/pdf",
                    "ContentLength": 168910,
                    "ContentID": "f_kejnjyug1",
                    "DownloadToken": "def",
                },
                {
                    "Name": "winter2020-2021.pdf",
                    "ContentType": "application\/pdf",
                    "ContentLength": 113007,
                    "ContentID": "f_kejnjyv02",
                    "DownloadToken": "xyz",
                },
            ],
            "Headers": {
                "Return-Path": "<antoine@mailclark.ai>",
                "Delivered-To": "test@clubble.me",
                "Received": [
                    "from spool.mail.gandi.net (spool5.mail.gandi.net [217.70.178.214]) by nmboxes20.sd4.0x35.net (Postfix) with ESMTP id 7115220256 for <test@clubble.me>; Tue,  1 Sep 2020 07:53:43 +0000 (UTC)",
                    "from sender4-of-o51.zoho.com (sender4-of-o51.zoho.com [136.143.188.51]) by spool.mail.gandi.net (Postfix) with ESMTPS id 4B618D80F65 for <test@clubble.me>; Tue,  1 Sep 2020 07:53:41 +0000 (UTC)",
                    "from mail-ot1-f42.google.com (mail-ot1-f42.google.com [209.85.210.42]) by mx.zohomail.com with SMTPS id 1598946814954566.0226921077056; Tue, 1 Sep 2020 00:53:34 -0700 (PDT)",
                    "by mail-ot1-f42.google.com with SMTP id a65so390247otc.8 for <test@clubble.me>; Tue, 01 Sep 2020 00:53:34 -0700 (PDT)",
                ],
                "ARC-Seal": "i=1; a=rsa-sha256; t=1598946818; cv=none;  d=zohomail.com; s=zohoarc;  b=A7jKTJCD9ieoEKAPtoZpyxtuJQp8ek0cIqCbf2HUvJkkVYmXIhI6jiLtYaR6Sm0Et5r\/E5vFPowt6RjFtWaDaz7UoW9CIiePJkEkGHgHhQ343s2IUWlADGGsCEPskwCvlJvn3tVSiABgQLIsf6FaqfkDZEOYtejRC786Jlb8eT8=",
                "ARC-Message-Signature": "i=1; a=rsa-sha256; c=relaxed\/relaxed; d=zohomail.com; s=zohoarc;  t=1598946818; h=Content-Type:Date:From:In-Reply-To:MIME-Version:Message-ID:References:Subject:To;  bh=CgBV\/y5azQ9uDe+uFDrdGKiTQx6DwkxdL1XwOip9ZEU=;  b=XuCp2CYwXDNo5dDdBML4beYI+IUT4+81Pr78RmDWpoaQfumm22YX3TF2tjITVtYnqmUDbLUoR4bBmPgrPIUWxsOc+omLlpg2FyjXO8Xyw\/MCazKZhrUuHaIvsMbV\/QOZLavGITgKtTVw8iMg2M1hVz8Ay8VKqG\/oFkbJxbzdZh8=",
                "ARC-Authentication-Results": "i=1; mx.zohomail.com; dkim=pass  header.i=mailclark.ai; spf=pass  smtp.mailfrom=antoine@mailclark.ai; dmarc=pass header.from=<antoine@mailclark.ai> header.from=<antoine@mailclark.ai>",
                "DKIM-Signature": "v=1; a=rsa-sha256; q=dns\/txt; c=relaxed\/relaxed; t=1598946818; s=zoho; d=mailclark.ai; i=antoine@mailclark.ai; h=MIME-Version:References:In-Reply-To:From:Date:Message-ID:Subject:To:Content-Type; bh=CgBV\/y5azQ9uDe+uFDrdGKiTQx6DwkxdL1XwOip9ZEU=; b=i4YJj1RFryuXbHDh8E9oKZv3+e6Kzat5oAxwuLZV4w\/t2b1rTBP\/qGMArXvuSRAz lNZvfJj4Kf7VD7nQMRrm8EdXGyuWPvVfjBU9PQjFs\/6GkANzLJW5PGGXZrlDXFIpiHH e5tmnYmFSfplAMsyZokpm5oDjT2whR34YZCGcUOg=",
                "X-Gm-Message-State": "AOAM530ChFmHzQDIPhTYzy4S5fs4ciUbgttaJYjt92mK62LXV52RGa7h zEkGPJ3KsDnCA7b9DrENpVFt\/zojNvW+Ha4nVbU=",
                "X-Google-Smtp-Source": "ABdhPJxFuLbNc8G\/rGIwkCPsDITPakKQW3VZe3+48by7auFyBNSjppLNydYymK21mcORQgOG5fYNeJkXu3+EPkerxj0=",
                "X-Received": "by 2002:a9d:58c8:: with SMTP id s8mr541588oth.292.1598946813444; Tue, 01 Sep 2020 00:53:33 -0700 (PDT)",
                "MIME-Version": "1.0",
                "References": "<e6df8cf2-cfb2-2cb6-320f-d9cba05a3001@clubble.me>",
                "In-Reply-To": "<e6df8cf2-cfb2-2cb6-320f-d9cba05a3001@clubble.me>",
                "From": "Antoine Lefeuvre <antoine@mailclark.ai>",
                "Date": "Tue, 1 Sep 2020 09:53:21 +0200",
                "X-Gmail-Original-Message-ID": "<CAN0zNmMsj_xOx8hCREv3rbovcYE3m5rZh8eRe+QSKC0yff_W6A@mail.gmail.com>",
                "Message-ID": "<CAN0zNmMsj_xOx8hCREv3rbovcYE3m5rZh8eRe+QSKC0yff_W6A@mail.gmail.com>",
                "Subject": "Re: Summer brochure 2021",
                "To": "Terry Estill <test@clubble.me>",
                "Content-Type": "multipart\/mixed",
                "X-Zoho-Virus-Status": "1",
                "X-ZohoMailClient": "External",
                "X-GND-Status": "LEGIT",
                "Received-SPF": "pass (spool5: domain of mailclark.ai designates 136.143.188.51 as permitted sender) client-ip=136.143.188.51; envelope-from=antoine@mailclark.ai; helo=sender4-of-o51.zoho.com;",
            },
        }
    ]
}


class InboundEmailParsingApiTest(TestCase):
    def test_inbound_parse_emails(self):
        url = reverse("api:inbound-email-parsing")
        response = self.client.post(url, data=EMAIL_JSON)
        self.assertEqual(response.status_code, 401)
