//
//  AppUserInfo.h
//  hookTest
//
//  Created by dev on 2018/4/17.
//

#import <Foundation/Foundation.h>
#include <UIKit/UIImage.h>
@interface AppUserInfo : NSObject<NSCoding>

@property(nonatomic,assign) NSInteger useMinutes;

@property(nonatomic,assign) BOOL bLocked;

@property(nonatomic,strong) NSDate *useDate;


@end
