"""Isolated native service lifecycle. No live tokens or Cloudflare calls."""
import hashlib
import io
import json
import os
from email.message import Message
from pathlib import Path
import tempfile
import unittest
import urllib.error
from activity_device import ActivityDevice, DeviceError, NoRedirect

class Response(io.BytesIO):
    def __init__(self,data):
        super().__init__(json.dumps(data).encode());self.headers=Message();self.headers['Content-Type']='application/json'
class Opener:
    def __init__(self): self.device=None;self.offline=False;self.revoked=False;self.wrong=False;self.requests=[]
    def open(self,req,timeout):
        self.requests.append(req)
        if self.offline: raise urllib.error.URLError('isolated offline')
        if self.revoked: raise urllib.error.HTTPError(req.full_url,401,'expired',{},io.BytesIO(b'{"error":"expired"}'))
        body=json.loads(req.data)
        if body['operation']=='revokeDevice':self.revoked=True;return Response({'revoked':True})
        return Response({'userId':'fixture-owner','spaceId':'foreign' if self.wrong else 'fixture-space','userName':'Fixture','isOwner':True,'device':{'id':self.device,'expiresAt':1900000000000}})
class DeviceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'private/device.json';self.opener=Opener();self.now=0
        self.d=ActivityDevice('https://fixture.example/cms/connect',self.path,self.opener,lambda:self.now)
    def tearDown(self):self.tmp.cleanup()
    def enroll(self):
        prepared=self.d.prepare();self.opener.device=prepared['device']['id'];self.d.commit(prepared['nonce']);return prepared
    def test_secret_never_crosses_browser_and_new_service_restores(self):
        p=self.enroll();self.assertEqual(set(p),{'nonce','device'});self.assertEqual(set(p['device']),{'id','label','tokenHash'})
        secret=self.d.credential()['token'];self.assertEqual(hashlib.sha256(secret.encode()).hexdigest(),p['device']['tokenHash']);self.assertNotIn(secret,json.dumps(p));self.assertEqual(self.path.stat().st_mode&0o777,0o600)
        second=ActivityDevice(self.d.origin+'/cms/connect',self.path,self.opener);self.assertTrue(second.status()['connected']);self.assertNotIn(secret,json.dumps(second.status()))
        self.assertEqual(self.opener.requests[-1].get_header('User-agent'),'YouyangContentStudio/1.0 (+https://youyang.art)')
        self.assertFalse(second.pending)
    def test_expired_pairing_is_not_saved(self):
        p=self.d.prepare();self.now=301
        with self.assertRaises(DeviceError) as e:self.d.commit(p['nonce'])
        self.assertEqual(e.exception.status,410);self.assertFalse(self.path.exists())
    def test_revoke_offline_preserves_credential_then_success_removes(self):
        self.enroll();self.opener.offline=True
        self.assertFalse(self.d.status()['connected']);self.assertTrue(self.d.status()['configured'])
        with self.assertRaises(DeviceError):self.d.forget()
        self.assertTrue(self.path.exists());self.opener.offline=False;self.d.forget();self.assertFalse(self.path.exists());self.assertTrue(self.opener.revoked)
    def test_wrong_scope_and_unknown_proxy_are_rejected(self):
        self.enroll();self.opener.wrong=True
        with self.assertRaises(DeviceError) as e:self.d.remote('state')
        self.assertEqual(e.exception.status,403)
        before=len(self.opener.requests)
        with self.assertRaises(DeviceError):self.d.remote('https://foreign.test')
        self.assertEqual(len(self.opener.requests),before)
    def test_other_users_and_symlink_cannot_read_credential(self):
        self.enroll();self.path.chmod(0o644)
        with self.assertRaises(DeviceError):self.d.credential()
        real=self.path.with_name('real');self.path.rename(real);self.path.symlink_to(real)
        with self.assertRaises(DeviceError):self.d.credential()
    def test_redirects_cannot_forward_bearer(self):
        with self.assertRaises(DeviceError):NoRedirect().redirect_request(None,None,None,None,None,None)
    def test_revoked_remote_credential_can_be_cleared(self):
        self.enroll();self.opener.revoked=True;self.d.forget();self.assertFalse(self.path.exists())
if __name__=='__main__':unittest.main()
