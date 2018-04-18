#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import zipfile
import os.path
import os
import time
import shutil
import subprocess
import plistlib
import sys,getopt

signextensions      = ['.framework/','.dylib','.appex/','.app/']
bundleidentifierkey = 'CFBundleIdentifier'
replaceplistkey     = 'BundleIdentifier'
oldbundleId         = None 
uncheckedfiles      = [] #暂未检查bundleId文件列表
certificatelist     = [] #证书列表
executableName      = None
version             = 'v1.0.0'

#用户参数
zipFilePath         = None
outputPath          = None
certificate         = None
mobileprovision     = None
entilement          = None
newBundleIdentifier = None

#拷贝mobileprovsion到xxx.app目录
def copyprovsion2appdir(originpath,mobileprovision):
	for dirpath, dirnames, filenames in os.walk(originpath):
		if dirpath[dirpath.rfind('.'):] == '.app':
			shutil.copy(mobileprovision,'%s/%s' % (dirpath,'embedded.mobileprovision'))
			return True
	return False

#根据mobileprovision生成entitlements.plist文件
def generateentitlements(mobileprovisionpath,entilementspath):
	entilementfull = entilementspath[:entilementspath.rfind('.')] + '_full.plist'
	(status1, output1) = subprocess.getstatusoutput('security cms -D -i "%s" > %s' % (mobileprovisionpath, entilementfull))
	(status2, output2) = subprocess.getstatusoutput('/usr/libexec/PlistBuddy -x -c "Print:Entitlements" %s > %s' % (entilementfull,entilementspath))
	return status1 == 0 and status2 == 0


#修改BundleIdentifier
def modifyBundleIdentifer(originpath,newBundleIdentifier):
	for dirpath,dirnames, filenames in os.walk(originpath):
		for filename in filenames:
			if os.path.split(filename)[-1] == 'Info.plist':
				modifyPlistBundleId(os.path.join(dirpath, filename),newBundleIdentifier)
	for filepath in uncheckedfiles:
		modifyPlistBundleId(filepath,newBundleIdentifier)

#修改Plist文件
def modifyPlistBundleId(filepath,newBundleIdentifier):
	with open(filepath, 'rb') as fp:
		pl = plistlib.load(fp)
		global oldbundleId
		if oldbundleId == None:
			oldbundleId = pl.get(bundleidentifierkey)
		if oldbundleId == None:
			uncheckedfiles.append(filepath)
			return
		for key in pl.keys():
			if replaceplistkey in key:
				pl[key] = pl[key].replace(oldbundleId,newBundleIdentifier)
			elif key == 'NSExtension' and 'NSExtensionAttributes' in pl['NSExtension'] and 'WKAppBundleIdentifier' in pl['NSExtension']['NSExtensionAttributes']:
				extAtts = pl['NSExtension']['NSExtensionAttributes']
				extAtts['WKAppBundleIdentifier'] = extAtts['WKAppBundleIdentifier'].replace(oldbundleId,newBundleIdentifier)
		with open(filepath, 'wb') as fp:
			plistlib.dump(pl, fp)

#获取证书列表
def getCertificates():
	try:
		(status,output) = subprocess.getstatusoutput('security find-identity -v -p codesigning')
		print(' 序号\t\t\tSHA-1\t\t\t证书名称')
		global certificatelist
		certificatelist = output.split('\n')
		certificatelist.pop(-1)
		print('\n'.join(certificatelist))
		return True
	except Exception as e:
		print(e)
		return False

#获取可执行文件名
def getExecutableName(originpath):
	for dirpath, dirnames, filenames in os.walk(originpath):
		if dirpath[dirpath.rfind('.'):] == '.app':
			return dirpath[dirpath.rfind(os.sep)+1:dirpath.rfind('.')]

#文件是否需要签名
def isneedsign(filename):
	for signextension in signextensions:
		if signextension == filename[filename.rfind('.'):] or executableName == filename[filename.rfind(os.sep)+1:]:
			return True
	return False

#签名
def codesign(certificate,entilement,signObj,extrapath):
	(status, output) = subprocess.getstatusoutput('codesign -f -s "%s" --entitlements "%s" "%s"' % (certificate,entilement,os.path.join(extrapath,signObj)))
	if status == 0:
		print('replacing %s existing signature successed' % signObj)
		return True
	else:
		print(output)
		return False

#开始签名
def startsign(certificate,entilement,zfilelist,extrapath):
	print("----------------开始签名----------------")
	for filename in zfilelist:
		if isneedsign(filename):
			if not codesign(certificate,entilement,filename,extrapath):
	 			return False
	if not codesign(certificate,entilement,os.path.join('Payload',executableName+'.app'),extrapath):
		return False
	return True

#zip压缩
def zipcompress(originpath,destinationzfile):
	resignedzfile = zipfile.ZipFile(destinationzfile,'w',zipfile.ZIP_DEFLATED)
	for dirpath, dirnames, filenames in os.walk(originpath):
		fpath = dirpath.replace(originpath,'')
		fpath = fpath and fpath + os.sep or ''
		for filename in filenames:
			resignedzfile.write(os.path.join(dirpath, filename), fpath+filename)
	resignedzfile.close()

#验证签名
def verifySignature(extralfilepath):
	for dirpath, dirnames, filenames in os.walk(extralfilepath):
		if dirpath[dirpath.rfind('.'):] == '.app':
			(status,output) = subprocess.getstatusoutput('codesign -v %s' % dirpath)
			if len(output) == 0:
				return True
			else:
				print(output)
				return False
	return False

#准备签名证书
def prepareCertificate():
	#获取证书列表
	if not getCertificates():
		return False

	try:
		certificateindexstr = input('请输入签名证书序号：').strip()
		certificateindex = int(certificateindexstr)
		if certificateindex < 1 or certificateindex > len(certificatelist):
			print('签名证书选择有误,请重试')
			return False
		else:
			selcert = certificatelist[certificateindex-1]
			global certificate
			certificate = selcert[selcert.find('"')+1:selcert.rfind('"')]
			print("你选择的签名证书是："+certificate)
	except Exception as e:
		print('签名证书选择有误,请重试')
		return False

#准备参数
def prepareArgsOptions():
	showhelp,showversion = False, False
	try:
		opts, args = getopt.getopt(sys.argv[1:],'hvi:o:c:p:e:b:')
	except Exception as e:
		print('参数不正确，请仔细检查！\n使用"resign -h"命令来查看帮助')
		sys.exit(0)
	for op, value in opts:
		if op == '-i':
			global zipFilePath
			zipFilePath = value
		elif op == '-o':
			global outputPath
			outputPath = value
		elif op == '-c':
			global certificate
			certificate = value
		elif op == '-p':
			global mobileprovision
			mobileprovision = value
		elif op == '-e':
			global entilement
			entilement = value
		elif op == '-b':
			global newBundleIdentifier
			newBundleIdentifier = value
		elif op == '-h':
			showhelp = True
		elif op == '-v':
			showversion = True
	if len(sys.argv) == 1 or showhelp:
		print('''
Usage: resign -i <input.ipa> -c "<certificate-name>" -p <provision-file-path>

where options are:
  -o <output-file-path>       resigned file output path
  -e <entitlements-file-path> entitlements.plist path
  -b <new-bundle-identifier>  new bundle id match with mobileprovsion
  -h                          show help information
  -v                          show resign tool version
			''')
		sys.exit(0)
	elif showversion:
		print(version)
		sys.exit(0)
	else:
		if zipFilePath == None:
			zipFilePath = input('请拖拽ipa到此：').strip()
		if certificate == None:
			prepareCertificate()
		if mobileprovision == None:
			mobileprovision = input('请拖拽mobileprovsion到此：').strip()
		if not os.path.isfile(zipFilePath):
			print('待签名ipa路径不正确，请仔细检查！')
			sys.exit(0)
		if not os.path.isfile(mobileprovision):
			print('mobileprovsion路径不正确，请仔细检查！')
			sys.exit(0)

def main():

	homedir = os.environ['HOME']
	extrapath = '%s/Payload_temp_%s/' % (homedir,str(time.time()))

	#准备参数
	prepareArgsOptions()

	global outputPath
	if outputPath == None:
		outputPath = zipFilePath[:zipFilePath.rfind('.')] + '_resigned.ipa'
	elif not '.ipa' in outputPath:
		if not os.path.exists(outputPath):
			print('输出文件路径有误，请仔细检查！')
			sys.exit(0)
			return
		outputPath = os.path.join(outputPath,zipFilePath[zipFilePath.rfind(os.sep)+1:zipFilePath.rfind('.')]+'_resigned.ipa')

	originzfile = zipfile.ZipFile(zipFilePath,'r')
	zfilelist = originzfile.namelist()
	zfilelist.reverse()

	#解压到临时目录
	originzfile.extractall(extrapath)

	#修改BundleIdentifier
	if newBundleIdentifier != None:
		modifyBundleIdentifer(extrapath,newBundleIdentifier)

	#拷贝mobileprovsion
	copyprovsion2appdir(extrapath, mobileprovision)

	global entilement
	if entilement == None:
		entilement = extrapath + "entitlements.plist"
		#生成entitlement.plist文件
		if not generateentitlements(mobileprovision,entilement):
			print("生成entitlements.plist文件失败!")
			#关闭zipfile
			originzfile.close()
			#删除临时解压目录
			shutil.rmtree(extrapath)
			return False
	
	#获取可执行文件名
	global executableName
	executableName = getExecutableName(extrapath)
	if executableName == None or executableName == '':
		print("获取可执行文件名失败!")
		#关闭zipfile
		originzfile.close()
		#删除临时解压目录
		shutil.rmtree(extrapath)
		return False

	try:
		#开始签名
		if zfilelist != None and startsign(certificate,entilement,zfilelist,extrapath):
			print("-------------签名完成，开始验证签名-------------")
			if verifySignature(extrapath):
				print("-------------验签成功，开始打包-------------")
				zipcompress(extrapath,outputPath)
				print("🚀 重签名打包成功,请查看：%s" % outputPath)
			else:
				print("-----------------验签失败，请重试---------------")
		else:
			print("----------------签名失败，请重试----------------")
	finally:
		#关闭zipfile
		originzfile.close()
		#删除临时解压目录
		shutil.rmtree(extrapath)

if __name__ == '__main__':
	main()