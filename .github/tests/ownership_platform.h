#import <Cocoa/Cocoa.h>
#import <Carbon/Carbon.h>
#import <ImageIO/ImageIO.h>

@interface OwnershipURL : NSObject
- (id)initWithString:(NSString *)text;
@property(readonly) OwnershipURL *URLByDeletingPathExtension;
- (OwnershipURL *)URLByAppendingPathExtension:(NSString *)extension;
- (NSString *)absoluteString;
@end
@interface OwnershipImage : NSObject
- (id)initWithContentsOfURL:(OwnershipURL *)url;
- (id)initWithIconRef:(IconRef)icon;
- (NSSize)size;
- (CGImageRef)CGImageForProposedRect:(NSRect *)rect context:(id)context hints:(id)hints;
@end
TISInputSourceRef OwnershipCurrent(void);
TISInputSourceRef OwnershipASCII(void);
TISInputSourceRef OwnershipLanguage(CFStringRef);
CFArrayRef OwnershipSources(CFDictionaryRef, Boolean);
OSStatus OwnershipSelect(TISInputSourceRef);
void *OwnershipProperty(TISInputSourceRef, CFStringRef);
CFURLRef OwnershipCreateURL(CFAllocatorRef, CFStringRef, CFURLPathStyle, Boolean);
CFStringRef OwnershipCopyPath(CFURLRef, CFURLPathStyle);
CGImageDestinationRef OwnershipDestination(CFMutableDataRef, CFStringRef, size_t, CFDictionaryRef);
void OwnershipAddImage(CGImageDestinationRef, CGImageRef, CFDictionaryRef);
bool OwnershipFinalize(CGImageDestinationRef);
void OwnershipScale(CGContextRef, CGFloat, CGFloat);
void OwnershipTranslate(CGContextRef, CGFloat, CGFloat);

#define NSURL OwnershipURL
#define NSImage OwnershipImage
#define TISCopyCurrentKeyboardInputSource OwnershipCurrent
#define TISCopyCurrentASCIICapableKeyboardInputSource OwnershipASCII
#define TISCopyInputSourceForLanguage OwnershipLanguage
#define TISCreateInputSourceList OwnershipSources
#define TISSelectInputSource OwnershipSelect
#define TISGetInputSourceProperty OwnershipProperty
#define CFURLCreateWithFileSystemPath OwnershipCreateURL
#define CFURLCopyFileSystemPath OwnershipCopyPath
#define CGImageDestinationCreateWithData OwnershipDestination
#define CGImageDestinationAddImage OwnershipAddImage
#define CGImageDestinationFinalize OwnershipFinalize
#define CGContextScaleCTM OwnershipScale
#define CGContextTranslateCTM OwnershipTranslate
