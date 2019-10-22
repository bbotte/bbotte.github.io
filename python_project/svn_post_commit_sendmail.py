#!/usr/bin/python
#coding=utf-8

from email.mime.text import MIMEText
from email.header import Header
import os
import smtplib

class SVNHook():
    def __init__(self, repository, revision):
        self.repository = repository
        self.revision = revision
        self.mail_host = 'XXX.com'
        self.mail_user = 'xxx@XXX.com'
        self.mail_pass = 'XXX'
        self.To = ['xxx@qq.com',]
        self.html_template = """
        <html>
                <h2 style="color:#FFFFFF; background: #008040;">基本信息</h2>
                <div> <b>版本库：</b>
                        <a href="svn:%s">%s</a>
                </div>
                <div> <b>版本号：</b>%s
                </div>
                <div>
                        <b>提交者：</b>%s
                </div>
                <div>
                        <b>提交时间：</b>%s
                </div>
                <h2 style="color:#FFFFFF; background: #4682B4;">提交说明</h2> <font size="4" color="#BF6000"><xmp>%s</xmp></font>
                <h2 style="color:#FFFFFF; background: #5353A8;">文件清单</h2>
                <xmp>%s</xmp>
                <hr>
                <center>
                        ☆ Powered by
                        <a href="http://garyelephant.me">Gary</a>
                </center>
                <center>
                        ☆ Inspired by
                        <a href="http://crearo-sw.blogspot.com">CREARO-SW</a>
                </center>
        </html>
        """

    def get_repo_name(self):
        return os.path.basename(self.repository)

    def get_author(self):
        cmd = '{0} author -r {1} {2}'.format('/usr/bin/svnlook', self.revision, self.repository)
        return os.popen(cmd).read()

    def get_date(self):
        cmd =  '{0} date -r {1} {2}'.format('/usr/bin/svnlook', self.revision, self.repository)
        return os.popen(cmd).read()

    def  get_log(self):
        cmd = '{0} log -r {1} {2}'.format('/usr/bin/svnlook', self.revision, self.repository)
        return os.popen(cmd).read()

    def get_file_list(self):
        cmd = '{0} changed -r {1} {2}'.format('/usr/bin/svnlook', self.revision, self.repository)
        return os.popen(cmd).read()

    def content(self):
        repository_name = self.get_repo_name()
        author = self.get_author()
        date = self.get_date()
        log = self.get_log()
        file_list = self.get_file_list()
        content = self.html_template %(repository, repository_name, revision, author, date, log, file_list)
        return content

    def send_mail(self):
        msg = MIMEText(self.content(), _subtype='html', _charset='utf-8')
        msg['Subject'] = Header('Subversion Hook Post-Commit Send MSG', 'utf-8')
        msg['From'] = 'test@kingsoft.com'
        msg['To'] = ';'.join(self.To)
        try:
            smtp = smtplib.SMTP(self.mail_host, 587)
            smtp.starttls()
            smtp.login(self.mail_user, self.mail_pass)
            smtp.sendmail(msg['From'], msg['To'], msg.as_string())
            smtp.close()
        except Exception, e:
            print str(e)

if __name__ == "__main__":
    repository = '/data/svn/pro1'
    revision = 2
    svnhook = SVNHook(repository, revision)
    svnhook.send_mail()
