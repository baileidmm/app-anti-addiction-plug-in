//
//  AppUserInfo.m
//  hookTest
//
//  Created by dev on 2018/4/17.
//

#import "AppUserInfo.h"

@implementation AppUserInfo


- (nullable instancetype)initWithCoder:(NSCoder *)aDecoder{
    
    if ([super init]) {
        self.useDate = [aDecoder decodeObjectForKey:@"useDate"];
        self.useMinutes = [aDecoder decodeIntegerForKey:@"useMinutes"];
        self.bLocked = [aDecoder decodeBoolForKey:@"bLocked"];
    }
    return self;
}

- (void)encodeWithCoder:(NSCoder *)aCoder{
    [aCoder encodeObject:self.useDate forKey:@"useDate"];
    [aCoder encodeInteger:self.useMinutes forKey:@"useMinutes"];
    [aCoder encodeBool:self.bLocked forKey:@"bLocked"];
}

@end
