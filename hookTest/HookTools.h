//
//  HookTools.h
//  hookTest
//
//  Created by dev on 2018/4/17.
//

#import <Foundation/Foundation.h>
#include <UIKit/UIImageView.h>



@interface HookTools : NSObject

@property (nonatomic, strong) dispatch_source_t timer;

@property (nonatomic, strong) UIImageView * remindView;
@property (nonatomic, assign) BOOL bShow;

+ (instancetype)shareInstance;

- (BOOL)isToday:(NSDate *)date;

@end
