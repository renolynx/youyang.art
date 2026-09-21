"""Revocable activity device credential. Never exposed to browser JS or public artifacts."""
import hashlib
import json
import os
from pathlib import Path
import secrets
import stat
import threading
import time
import urllib.error
import urllib.request
from urllib.parse import urlsplit

class DeviceError(ValueError):
    def __init__(self,message,status=503): super().__init__(message);self.status=status

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): raise DeviceError('活动服务地址发生跳转，请核对正式站点')

class ActivityDevice:
    def __init__(self,broker_url,state_path=None,opener=None,clock=None):
        url=urlsplit(broker_url)
        if url.path!='/cms/connect' or url.username or url.password or url.query or url.fragment or not url.hostname or (url.scheme!='https' and not (url.scheme=='http' and url.hostname in ('localhost','127.0.0.1'))):
            raise ValueError('活动设备必须绑定固定的正式连接地址')
        self.origin=url.scheme+'://'+url.netloc
        self.path=Path(state_path) if state_path else Path.home()/'Library/Application Support/Youyang Content Studio/activity-device.json'
        self.opener=opener or urllib.request.build_opener(NoRedirect())
        self.clock=clock or time.monotonic
        self.lock=threading.RLock();self.pending={}

    def credential(self):
        try:
            fd=os.open(self.path,os.O_RDONLY|os.O_NOFOLLOW)
        except FileNotFoundError: return None
        except OSError: raise DeviceError('本机授权文件无法安全读取',403) from None
        with os.fdopen(fd,'r') as source:
            info=os.fstat(source.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or info.st_mode & 0o077:
                raise DeviceError('本机授权文件权限不正确；需要仅当前用户可读写',403)
            try: value=json.loads(source.read(8192))
            except (ValueError,UnicodeError): raise DeviceError('本机授权文件损坏，请重新授权',403) from None
        if not isinstance(value,dict) or value.get('origin')!=self.origin or not isinstance(value.get('token'),str):
            raise DeviceError('本机授权不属于当前活动站点',403)
        return value

    def remote(self,operation,payload=None,credential=None):
        if operation not in ('state','command','photo','removePhoto','reconcilePhotos','revokeDevice'):
            raise DeviceError('不支持此项本机操作',400)
        value=credential or self.credential()
        if not value: raise DeviceError('请先连接组织者账号并授权这台电脑',401)
        body=json.dumps({'operation':operation,'payload':payload},ensure_ascii=False).encode()
        if len(body)>65536: raise DeviceError('活动请求过大',413)
        req=urllib.request.Request(self.origin+'/api/cms/device',body,method='POST',headers={
            'Authorization':'Bearer '+value['token'],'Content-Type':'application/json',
            'Accept':'application/json,image/jpeg,image/png,image/webp',
            'User-Agent':'YouyangContentStudio/1.0 (+https://youyang.art)'})
        try:
            with self.opener.open(req,timeout=28) as response:
                mime=response.headers.get_content_type();data=response.read(5*1024*1024+1)
                if len(data)>5*1024*1024: raise DeviceError('活动响应超过大小限制',413)
                if operation=='photo':
                    if mime not in ('image/jpeg','image/png','image/webp'): raise DeviceError('照片格式无效')
                    return data,mime
                try: result=json.loads(data)
                except (ValueError,UnicodeError): raise DeviceError('活动服务返回无效响应；保存结果未知，请用原操作重试。') from None
                if not isinstance(result,dict): raise DeviceError('活动服务返回无效响应')
                if operation!='revokeDevice' and (result.get('userId')!=value.get('userId',result.get('userId')) or result.get('spaceId')!=value.get('spaceId',result.get('spaceId'))):
                    raise DeviceError('活动账号或空间与本机授权不一致',403)
                return result
        except urllib.error.HTTPError as error:
            # Do not expose request headers, credentials or arbitrary upstream HTML.
            try: message=json.loads(error.read(65536)).get('error')
            except (ValueError,UnicodeError,AttributeError): message=None
            raise DeviceError(message if isinstance(message,str) and len(message)<1000 else '活动服务暂时不可用，请保留输入后重试',error.code) from None
        except (urllib.error.URLError,TimeoutError,OSError) as error:
            raise DeviceError('网络暂时不可用；授权仍保留，恢复后可重试。保存结果未知时请用原操作重试。') from None

    def status(self):
        if not self.credential(): return {'configured':False,'connected':False}
        try:
            data=self.remote('state')
            return {'configured':True,'connected':True,'userName':data['userName'],'spaceId':data['spaceId'],'device':data['device']}
        except DeviceError as e:return {'configured':True,'connected':False,'error':str(e),'status':e.status}

    def prepare(self):
        with self.lock:
            self.pending={key:value for key,value in self.pending.items() if value['until']>self.clock()}
            if self.credential(): raise DeviceError('本机已经有授权；先恢复连接或解除原授权',409)
            if len(self.pending)>=4: raise DeviceError('正在处理本机授权，请稍后重试',429)
            device_id=secrets.token_hex(16);token='ysd_'+device_id+'_'+secrets.token_urlsafe(32);nonce=secrets.token_urlsafe(24)
            self.pending[nonce]={'origin':self.origin,'token':token,'id':device_id,'until':self.clock()+300}
            return {'nonce':nonce,'device':{'id':device_id,'tokenHash':hashlib.sha256(token.encode()).hexdigest(),'label':'本机内容台 · Mac'}}

    def commit(self,nonce):
        with self.lock:
            value=self.pending.get(nonce)
            if not value or value['until']<=self.clock(): raise DeviceError('本机授权请求已过期，请重新发起',410)
            if self.credential(): raise DeviceError('本机授权已改变，请刷新内容台',409)
            data=self.remote('state',credential=value)
            if data.get('device',{}).get('id')!=value['id'] or not data.get('isOwner'):
                raise DeviceError('服务未确认这台电脑的组织者授权',403)
            stored={key:value[key] for key in ('origin','token','id')}
            stored.update(userId=data['userId'],spaceId=data['spaceId'])
            self.path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
            if self.path.parent.is_symlink(): raise DeviceError('授权目录不可使用符号链接',403)
            temporary=self.path.with_name(self.path.name+'.'+secrets.token_hex(8))
            fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
            try:
                with os.fdopen(fd,'w') as target:
                    json.dump(stored,target);target.flush();os.fsync(target.fileno())
                os.replace(temporary,self.path)
            finally:
                if temporary.exists():temporary.unlink()
            del self.pending[nonce]
            return {'connected':True,'userName':data['userName'],'spaceId':data['spaceId'],'device':data['device']}

    def forget(self):
        with self.lock:
            if self.credential():
                try:self.remote('revokeDevice')
                except DeviceError as e:
                    if e.status not in (401,403):raise
                self.path.unlink(missing_ok=True)
            self.pending.clear()
            return {'configured':False,'connected':False}
