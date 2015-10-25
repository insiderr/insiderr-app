//
//  main.m
//  insiderr
//

#import <Foundation/Foundation.h>
#import <UIKit/UIKit.h>
//#include <python2.7/Python.h>
//#include <Python.h>
#include "../dist/root/python/include/python2.7/Python.h"
#include "../dist/include/common/sdl2/SDL_main.h"
#include <dlfcn.h>

#import <Foundation/Foundation.h>
#import "FDStatusBarNotifierView.h"
#import <Social/Social.h>

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

@interface ObjcClassINSD : NSObject {
    UIWebView *webView;
}
@property(nonatomic, readwrite, assign) NSString * aParam1;
@property(nonatomic, readwrite, assign) NSString * aParam2;
@property(nonatomic, readwrite, assign) NSString * aParam3;
- (void) openWebView;
- (void) closeWebView;
- (void) lightStatusBar;
@end

@implementation ObjcClassINSD

- (void) lightStatusBar {
    // Change status bar color to light, we might need SDL Support here -- check SDL_uikitappdelegate.m
    [[UIApplication sharedApplication] setStatusBarHidden:NO];
    [[UIApplication sharedApplication] setStatusBarStyle:UIStatusBarStyleLightContent];
}

- (void) openWebView {
    webView = [[UIWebView alloc] initWithFrame:CGRectMake(0, 0, 320, 360)];
    
    //[webView setDelegate:[[[UIApplication sharedApplication] windows] lastObject]];
    UIWindow *mainWindow = [[UIApplication sharedApplication] keyWindow];
    [webView setDelegate: (id<UIWebViewDelegate>)mainWindow];
    
    NSString *aURLstr = _aParam1;
    NSURL *url = [NSURL URLWithString:aURLstr];
    NSURLRequest *requestObj = [NSURLRequest requestWithURL:url];
    [webView loadRequest:requestObj];
    
    //[[[[UIApplication sharedApplication] windows] lastObject] addSubview:webView];
    [mainWindow addSubview:webView];
}

- (void) closeWebView {
    [webView removeFromSuperview];
}

@end

////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


@interface ToastINSD : NSObject {
    FDStatusBarNotifierView *notifierView;
}
@property(nonatomic, readwrite, assign) NSString * aText;
- (void) showToastBar;
@end

@implementation ToastINSD
- (void) showToastBar {
    UIWindow *mainWindow = [[UIApplication sharedApplication] keyWindow];
    if (notifierView==nil) {
        notifierView = [[FDStatusBarNotifierView alloc] initWithMessage:_aText];
    }
    notifierView.message = _aText;
    notifierView.timeOnScreen = 3.0;
    if (notifierView.isHidden) {
        [notifierView showInWindow:mainWindow];
    }
}
@end

////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

@interface ShareViewControllerINDR : UIViewController{
}
@property(nonatomic, readwrite, assign) NSString * aApp;
@property(nonatomic, readwrite, assign) NSString * aURL;
@property(nonatomic, readwrite, assign) NSString * aFileName;
@property(nonatomic, readwrite, assign) NSString * aTitle;
- (void) shareImagePost;
@end

@implementation ShareViewControllerINDR

- (void) shareImagePost{
    NSString *text = _aTitle;
    NSURL *url = [NSURL URLWithString:_aURL];
    UIImage *image = [UIImage imageWithContentsOfFile:_aFileName];
    
    SLComposeViewController *controllerSC = nil;
    NSString* UTI = nil;
    NSString* filePath = _aFileName;
    if (_aApp!=nil)
    {
        NSString *action = _aApp;
        if ([action caseInsensitiveCompare:@"facebook"]==NSOrderedSame)
        {
            // facebook
            controllerSC = [SLComposeViewController composeViewControllerForServiceType:SLServiceTypeFacebook];
        }
        else if ([action caseInsensitiveCompare:@"twitter"]==NSOrderedSame)
        {
            // twitter
            controllerSC = [SLComposeViewController composeViewControllerForServiceType:SLServiceTypeTwitter];
        }
        else if ([action caseInsensitiveCompare:@"whatsapp"]==NSOrderedSame)
        {
            // whatsapp
            NSString * msg = _aURL;
            if (msg==nil){
                msg=@"";
            }
            if (text==nil){
                text=@"";
            }
            NSString * urlWhats = [NSString stringWithFormat:@"whatsapp://send?text=%@%@",text,msg];
            NSURL * whatsappURL = [NSURL URLWithString:[urlWhats stringByAddingPercentEscapesUsingEncoding:NSUTF8StringEncoding]];
            if ([[UIApplication sharedApplication] canOpenURL: whatsappURL])
            {
                if (image!=nil)
                {
                    UTI = @"net.whatsapp.image";
                    NSString *filePath  = [NSHomeDirectory() stringByAppendingPathComponent:@"Documents/whatsAppTmp.wai"];
                    [UIImageJPEGRepresentation(image, 1.0) writeToFile:filePath atomically:YES];
                }
                else
                {
                    [[UIApplication sharedApplication] openURL: whatsappURL];
                    return;
                }
            }
        }
        else if ([action caseInsensitiveCompare:@"linkedin"]==NSOrderedSame)
        {
            // linkedin
            UTI = @"linkedin.com";
        }
        else if ([action caseInsensitiveCompare:@"message"]==NSOrderedSame)
        {
            // message mms
        }
        else if ([action caseInsensitiveCompare:@"link"]==NSOrderedSame)
        {
            // link only
        }
        else {
            // default share
            //UTI = @"";
        }
    }
    
    if (controllerSC!=nil){
        if (text!=nil){
            [controllerSC setInitialText:text];
        }
        if (text!=nil){
            [controllerSC addURL:url];
        }
        if (text!=nil){
            [controllerSC addImage:image];
        }
        
        [controllerSC setCompletionHandler:^(SLComposeViewControllerResult result) {
            [self.view removeFromSuperview];
        }];
        
        [self setModalPresentationStyle:UIModalPresentationPageSheet];
        UIWindow *mainWindow = [[UIApplication sharedApplication] keyWindow];
        [mainWindow addSubview:self.view];
        [self presentViewController:controllerSC animated:YES completion:nil];
        
    }
    else if (UTI!=nil && filePath!=nil)
    {
        UIDocumentInteractionController* weakDocumentInteraction;
        weakDocumentInteraction = [UIDocumentInteractionController interactionControllerWithURL:[NSURL fileURLWithPath:filePath]];
        
        if (text!=nil && url!=nil){
            //weakDocumentInteraction.annotation = @{@"url": _aURL, @"title":text, @"caption":text,@"message":_aURL,@"link":_aURL,@"text":text};
            weakDocumentInteraction.annotation = [NSString stringWithFormat:@"%@ %@",text, _aURL];
        }
        else if (text!=nil){
            //weakDocumentInteraction.annotation = @{@"title":text, @"caption":text,@"message":text, @"text":text};
            weakDocumentInteraction.annotation = [NSString stringWithFormat:@"%@",text];
        }
        else if (url!=nil){
            //weakDocumentInteraction.annotation = @{@"url": _aURL, @"title":_aURL, @"caption":_aURL,@"link":_aURL,@"text":_aURL};
            weakDocumentInteraction.annotation = [NSString stringWithFormat:@"%@", _aURL];
        }
        
        if (UTI.length > 0) {
            weakDocumentInteraction.UTI = UTI;
        }
        __weak __typeof__(self) weakSelf = self;
        weakDocumentInteraction.delegate = weakSelf;
        
        [weakDocumentInteraction retain];
        UIWindow *keyWindow= [[UIApplication sharedApplication] keyWindow];
        UIViewController *mainController = [keyWindow rootViewController];
        CGRect rectDocC = CGRectMake(0, 0, 320, 360);
        [weakDocumentInteraction presentOptionsMenuFromRect:rectDocC inView:mainController.view  animated:YES];
    }
    else
    {
        NSArray* shares = @[text];
        if (url!=nil) {
            shares = @[text, url];
        }
        if (image!=nil && url!=nil) {
            shares = @[text, url, image];
        }
        if (image!=nil && url==nil) {
            shares = @[text, image];
        }
        
        UIActivityViewController *controller =
        [[UIActivityViewController alloc]
         initWithActivityItems:shares
         applicationActivities:nil];
        
        [controller setCompletionHandler:^(NSString *activityType, BOOL completed) {
            [self.view removeFromSuperview];
        }];
        
        [self setModalPresentationStyle:UIModalPresentationPageSheet];
        UIWindow *mainWindow = [[UIApplication sharedApplication] keyWindow];
        [mainWindow addSubview:self.view];
        [self presentViewController:controller animated:YES completion:nil];
    }
    
    _aApp=nil;
    _aURL=nil;
    _aFileName=nil;
    _aTitle=nil;
}

@end

////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

void export_orientation();
void load_custom_builtin_importer();

int main(int argc, char *argv[]) {
    int ret = 0;
    
    NSAutoreleasePool * pool = [[NSAutoreleasePool alloc] init];

    // Change the executing path to YourApp
    chdir("YourApp");
    
    // Special environment to prefer .pyo, and don't write bytecode if .py are found
    // because the process will not have write attribute on the device.
    putenv("PYTHONOPTIMIZE=2");
    putenv("PYTHONDONTWRITEBYTECODE=1");
    putenv("PYTHONNOUSERSITE=1");
    putenv("PYTHONPATH=.");
    //putenv("PYTHONVERBOSE=1");
    
    // Kivy environment to prefer some implementation on ios platform
    putenv("KIVY_BUILD=ios");
    putenv("KIVY_NO_CONFIG=1");
    putenv("KIVY_NO_FILELOG=1");
    putenv("KIVY_WINDOW=sdl2");
    putenv("KIVY_IMAGE=imageio,tex");
    putenv("KIVY_AUDIO=sdl2");
    #ifndef DEBUG
    //putenv("KIVY_NO_CONSOLELOG=1");
    #endif
    
    // Export orientation preferences for Kivy
    export_orientation();

    NSString * resourcePath = [[NSBundle mainBundle] resourcePath];
    NSLog(@"PythonHome is: %s", (char *)[resourcePath UTF8String]);
    Py_SetPythonHome((char *)[resourcePath UTF8String]);

    NSLog(@"Initializing python");
    Py_Initialize();    
    PySys_SetArgv(argc, argv);

    // If other modules are using thread, we need to initialize them before.
    PyEval_InitThreads();

    // Add an importer for builtin modules
    load_custom_builtin_importer();

    // Search and start main.py
    const char * prog = [
        [[NSBundle mainBundle] pathForResource:@"YourApp/main" ofType:@"pyo"] cStringUsingEncoding:
        NSUTF8StringEncoding];
    NSLog(@"Running main.pyo: %s", prog);
    FILE* fd = fopen(prog, "r");
    if ( fd == NULL ) {
        ret = 1;
        NSLog(@"Unable to open main.pyo, abort.");
    } else {
        ret = PyRun_SimpleFileEx(fd, prog, 1);
        if (ret != 0)
            NSLog(@"Application quit abnormally!");
    }
    
    Py_Finalize();
    NSLog(@"Leaving");
    
    [pool release];
    
    // Look like the app still runn even when we leaved here.
    exit(ret);
    return ret;
}

// This method read available orientations from the Info.plist, and share them
// in an environment variable. Kivy will automatically set the orientation
// according to this environment value, if exist.
void export_orientation() {
    NSDictionary *info = [[NSBundle mainBundle] infoDictionary];
    NSArray *orientations = [info objectForKey:@"UISupportedInterfaceOrientations"];
    NSString *result = [[NSString alloc] initWithString:@"KIVY_ORIENTATION="];
    for (int i = 0; i < [orientations count]; i++) {
        NSString *item = [orientations objectAtIndex:i];
        item = [item substringFromIndex:22];
        if (i > 0)
            result = [result stringByAppendingString:@" "];
        result = [result stringByAppendingString:item];
    }

    putenv((char *)[result UTF8String]);
    NSLog(@"Available orientation: %@", result);
}

void load_custom_builtin_importer() {
    static const char *custom_builtin_importer = \
        "import sys, imp\n" \
        "from os import environ\n" \
        "from os.path import exists, join\n" \
        "# Fake redirection when we run the app without xcode\n" \
        "if 'CFLOG_FORCE_STDERR' not in environ:\n" \
        "    class fakestd(object):\n" \
        "        def write(self, *args, **kw): pass\n" \
        "        def flush(self, *args, **kw): pass\n" \
        "    sys.stdout = fakestd()\n" \
        "    sys.stderr = fakestd()\n" \
        "# Custom builtin importer for precompiled modules\n" \
        "class CustomBuiltinImporter(object):\n" \
        "    def find_module(self, fullname, mpath=None):\n" \
        "        if '.' not in fullname:\n" \
        "            return\n" \
        "        if mpath is None:\n" \
        "            return\n" \
        "        part = fullname.rsplit('.')[-1]\n" \
        "        fn = join(mpath[0], '{}.so'.format(part))\n" \
        "        if exists(fn):\n" \
        "            return self\n" \
        "        return\n" \
        "    def load_module(self, fullname):\n" \
        "        f = fullname.replace('.', '_')\n" \
        "        mod = sys.modules.get(f)\n" \
        "        if mod is None:\n" \
        "            #print 'LOAD DYNAMIC', f, sys.modules.keys()\n" \
        "            try:\n" \
        "                mod = imp.load_dynamic(f, f)\n" \
        "            except ImportError:\n" \
        "                #print 'LOAD DYNAMIC FALLBACK', fullname\n" \
        "                mod = imp.load_dynamic(fullname, fullname)\n" \
        "            return mod\n" \
        "        return mod\n" \
        "sys.meta_path.append(CustomBuiltinImporter())";
    PyRun_SimpleString(custom_builtin_importer);
}
