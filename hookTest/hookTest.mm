//
//  hookTest.mm
//  hookTest
//
//  Created by dev on 2018/4/17.
//  Copyright (c) 2018年 ___ORGANIZATIONNAME___. All rights reserved.
//

// CaptainHook by Ryan Petrich
// see https://github.com/rpetrich/CaptainHook/

#import <Foundation/Foundation.h>
#import "CaptainHook/CaptainHook.h"
#include <UIKit/UIKit.h> // not required; for examples only
#include <UIKit/UIView.h>
#include <UIKit/UILabel.h>
#include "AppUserInfo.h"
#include "HookTools.h"

// Objective-C runtime hooking using CaptainHook:
//   1. declare class using CHDeclareClass()
//   2. load class using CHLoadClass() or CHLoadLateClass() in CHConstructor
//   3. hook method using CHOptimizedMethod()
//   4. register hook using CHHook() in CHConstructor
//   5. (optionally) call old method using CHSuper()

//app 防沉迷插件开发
//添加一个遮挡窗口  当一天内使用时间超过 指定时间  显示遮挡窗口禁止操作

//判断当天使用时间
//添加一个持久化文件 保存 日期 已经使用时间

//程序进入前台时先读取日期和时间  如果日期 小于当前日期  使用时长清0  大于的话 直接 显示遮挡窗口

//启动定时器 每分钟 判断时间是否超时  并保存到文件


@class AppDelegate;

#define limitTimes  60

CHDeclareClass(AppDelegate); // declare class

CHOptimizedMethod(1, self, void, AppDelegate, applicationDidBecomeActive,UIApplication *,arg1) // hook method (with no arguments and no return value)
{
	// write code here ...
	
	CHSuper(1, AppDelegate, applicationDidBecomeActive,arg1); // call old (original) method
    NSLog(@"hook applicationDidBecomeActive!!!");
    NSString *file = [NSSearchPathForDirectoriesInDomains(NSDocumentDirectory, NSUserDomainMask, YES).firstObject stringByAppendingPathComponent:@"appuser.data"];
    AppUserInfo *userInfo = [NSKeyedUnarchiver unarchiveObjectWithFile:file];
    if (!userInfo) {
        NSLog(@"not find userInfo!!!");
        userInfo = [[AppUserInfo alloc]init];
        userInfo.useMinutes = 0;
        userInfo.useDate = [NSDate date];
        userInfo.bLocked = NO;
    }
    
    BOOL isToday =  [[HookTools shareInstance]isToday:userInfo.useDate];
    
    if (!isToday) {
        NSLog(@"not today userInfo!!!");
        userInfo.useMinutes = 0;
        userInfo.useDate = [NSDate date];
        userInfo.bLocked = NO;
        [NSKeyedArchiver archiveRootObject:userInfo toFile:file];
        if ([HookTools shareInstance].bShow) {
            [[HookTools shareInstance].remindView removeFromSuperview];
            [HookTools shareInstance].bShow = NO;
        }
    }
    
    dispatch_block_t addViewBlock = ^{
        
        NSLog(@"addView now!!!");
        [[HookTools shareInstance].remindView setFrame:arg1.keyWindow.bounds];
        [arg1.keyWindow addSubview:[HookTools shareInstance].remindView];
        [arg1.keyWindow bringSubviewToFront:[HookTools shareInstance].remindView];
        [HookTools shareInstance].bShow = YES;
        NSLog(@"addView success");
    };
    
    
    if (isToday&&YES == userInfo.bLocked&&![HookTools shareInstance].bShow) {
        
        addViewBlock();
        return;
    }
    
    if(!userInfo.bLocked&&nil == [HookTools shareInstance].timer){
        //开启定时器
        NSLog(@"create timer!!!");
        dispatch_queue_t queue = dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_DEFAULT, 0);
         [HookTools shareInstance].timer  = dispatch_source_create(DISPATCH_SOURCE_TYPE_TIMER,0, 0, queue);
        dispatch_source_set_timer([HookTools shareInstance].timer, dispatch_walltime(NULL, 0), (uint64_t)(60 *NSEC_PER_SEC), 0);
        // 设置回调
        dispatch_source_set_event_handler([HookTools shareInstance].timer, ^{
            
            AppUserInfo *userInfo = [NSKeyedUnarchiver unarchiveObjectWithFile:file];
            if (!userInfo) {
                userInfo = [[AppUserInfo alloc]init];
                userInfo.useMinutes = 0;
                userInfo.useDate = [NSDate date];
                userInfo.bLocked = NO;
            }
            
            NSLog(@"time coming now count is %lu",userInfo.useMinutes);
            
            userInfo.useMinutes++;
            if (userInfo.useMinutes >= limitTimes) {
                NSLog(@"app use timeout!!!");
              dispatch_async(dispatch_get_main_queue(),addViewBlock);
                userInfo.bLocked = YES;
                dispatch_cancel([HookTools shareInstance].timer);
                [HookTools shareInstance].timer = nil;
            }
            [NSKeyedArchiver archiveRootObject:userInfo toFile:file];
        });
    }
    if([HookTools shareInstance].timer){
        NSLog(@"resume timer!!!");
        dispatch_resume([HookTools shareInstance].timer);
    }
}

CHOptimizedMethod(1, self, void, AppDelegate, applicationDidEnterBackground,UIApplication *,arg1){
    CHSuper(1, AppDelegate, applicationDidEnterBackground,arg1);
    NSLog(@"hook applicationDidEnterBackground!!!");
    if([HookTools shareInstance].timer){
        NSLog(@"suspend timer!!!");
        dispatch_suspend([HookTools shareInstance].timer);
    }
}


CHConstructor // code block that runs immediately upon load
{
	@autoreleasepool
	{
		// listen for local notification (not required; for example only)
		
		// CHLoadClass(ClassToHook); // load class (that is "available now")
		CHLoadLateClass(AppDelegate);  // load class (that will be "available later")
		CHHook(1, AppDelegate, applicationDidBecomeActive); // register hook
        CHHook(1, AppDelegate, applicationDidEnterBackground);
        
	}
}
