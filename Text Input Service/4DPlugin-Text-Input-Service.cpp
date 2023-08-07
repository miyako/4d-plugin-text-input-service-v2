/* --------------------------------------------------------------------------------
 #
 #  4DPlugin-Text-Input-Service.cpp
 #	source generated by 4D Plugin Wizard
 #	Project : Text Input Service
 #	author : miyako
 #	2023/08/07
 #  
 # --------------------------------------------------------------------------------*/

#include "4DPlugin-Text-Input-Service.h"

#pragma mark -

void PluginMain(PA_long32 selector, PA_PluginParameters params) {
    
	try
	{
        switch(selector)
        {
			// --- Text Input Service
            
			case 1 :
                PA_RunInMainProcess((PA_RunInMainProcessProcPtr)INPUT_SET_SOURCE, params);
				break;
			case 2 :
                PA_RunInMainProcess((PA_RunInMainProcessProcPtr)INPUT_Get_source, params);
				break;
			case 3 :
                INPUT_SOURCE_LIST(params);
				break;

        }

	}
	catch(...)
	{

	}
}

#pragma mark -

void INPUT_SET_SOURCE(PA_PluginParameters params) {

    PackagePtr pParams = (PackagePtr)params->fParameters;
    C_TEXT Param1;
    Param1.fromParamAtIndex(pParams, 1);
    
    TISInputSourceRef source = nil;
    
    if(Param1.getUTF16Length() == 0){
        source = TISCopyCurrentASCIICapableKeyboardInputSource();
    }else{
        NSString *language = Param1.copyUTF16String();
        if([language isEqualToString:@"ASCII"]){
            source = TISCopyCurrentASCIICapableKeyboardInputSource();
        }else{
            CFArrayRef sources = TISCreateInputSourceList(NULL, NO);
            if(sources)
            {
                CFIndex i, count = CFArrayGetCount(sources);
                TISInputSourceRef s;
                for (i = 0; i < count; ++i)
                {
                    s = (TISInputSourceRef)CFArrayGetValueAtIndex(sources, i);
                    if(s != nil)
                    {
                        if(CFStringCompare((CFStringRef)language,
                        (CFStringRef)TISGetInputSourceProperty(s, kTISPropertyInputSourceID),
                        kCFCompareAnchored|kCFCompareBackwards) == kCFCompareEqualTo)
                        {
                            source = (TISInputSourceRef)CFRetain(s);
                            break;
                        }
                    }
                }
                CFRelease(sources);
            }
            if(source == nil)
            {
                source = TISCopyInputSourceForLanguage((CFStringRef)language);
            }
        }
        [language release];
    }
    
    if(source) {
        /*
         *      If there is more than one such input source
         *      and at least one has previously been used, then the
         *      most-recently-used one will be chosen
         */
        TISSelectInputSource(source);
        CFRelease(source);
    }
}

void INPUT_Get_source(PA_PluginParameters params) {
    
    PackagePtr pParams = (PackagePtr)params->fParameters;
    sLONG_PTR *pResult = (sLONG_PTR *)params->fResult;
    C_TEXT Param1, returnValue;
    Param1.fromParamAtIndex(pParams, 1);
    
    TISInputSourceRef source = nil;

    if(Param1.getUTF16Length() == 0){
        source = TISCopyCurrentKeyboardInputSource();
    }else{
        NSString *language = Param1.copyUTF16String();
        
        if([language isEqualToString:@"ASCII"]){
            source = TISCopyCurrentASCIICapableKeyboardInputSource();
        }else{
            source = TISCopyInputSourceForLanguage((CFStringRef)language);
        }
        
        [language release];
    }
    
    if(source) {
        NSString *identifier = (NSString *)TISGetInputSourceProperty(source, kTISPropertyInputSourceID);
        returnValue.setUTF16String(identifier);
        CFRelease(source);
    }
    
    returnValue.setReturn(pResult);
}

static void _input_sources_list(NSMutableArray *list) {
 
    CFArrayRef sources = TISCreateInputSourceList(NULL, NO);
    if(sources)
    {
        CFIndex i, count = CFArrayGetCount(sources);
        TISInputSourceRef s;
        for (i = 0; i < count; ++i)
        {
            s = (TISInputSourceRef)CFArrayGetValueAtIndex(sources, i);
            if(s != nil)
            {
                NSMutableDictionary *dict = [[NSMutableDictionary alloc]init];
                
                NSString *category = (NSString *)TISGetInputSourceProperty(s, kTISPropertyInputSourceCategory);
                if(category != nil) [dict setObject:category forKey:@"category"];

                NSString *name = (NSString *)TISGetInputSourceProperty(s, kTISPropertyLocalizedName);
                if(name != nil) [dict setObject:name forKey:@"name"];
                
                NSString *type = (NSString *)TISGetInputSourceProperty(s, kTISPropertyInputSourceType);
                if(type != nil) [dict setObject:type forKey:@"type"];
                                
                NSString *inputSourceID = (NSString *)TISGetInputSourceProperty(s, kTISPropertyInputSourceID);
                if(inputSourceID != nil) [dict setObject:inputSourceID forKey:@"inputSourceID"];
                
                NSString *bundleID = (NSString *)TISGetInputSourceProperty(s, kTISPropertyBundleID);
                if(bundleID != nil) [dict setObject:bundleID forKey:@"bundleID"];
                                
                NSString *inputModeID = (NSString *)TISGetInputSourceProperty(s, kTISPropertyInputModeID);
                if(inputModeID != nil) [dict setObject:inputModeID forKey:@"inputModeID"];
                                
                NSImage *icon;
                
                NSURL *url = (NSURL *)TISGetInputSourceProperty(s, kTISPropertyIconImageURL);
                if(url)
                {
                    icon = [[NSImage alloc]initWithContentsOfURL:url];
                    
                    if(!icon){
                        //the extension is sometimes wrong; try again png -> tiff
                        url = [url.URLByDeletingPathExtension URLByAppendingPathExtension:@"tiff"];
                        icon = [[NSImage alloc]initWithContentsOfURL:url];
                    }
                    
                    if(icon){
                        //return picture without memory leak; avoid the use of - TIFFRepresentation
                        NSRect imageRect = NSMakeRect(0, 0, icon.size.width , icon.size.height);
                        CGImageRef image = [icon CGImageForProposedRect:(NSRect *)&imageRect context:NULL hints:NULL];
                        CFMutableDataRef data = CFDataCreateMutable(kCFAllocatorDefault, 0);
                        CGImageDestinationRef destination = CGImageDestinationCreateWithData(data, kUTTypeTIFF, 1, NULL);
                        CFMutableDictionaryRef properties = CFDictionaryCreateMutable(kCFAllocatorDefault, 0, NULL, NULL);
                        CGImageDestinationAddImage(destination, image, properties);
                        CGImageDestinationFinalize(destination);
                        [dict setObject:[(NSData *)data base64EncodedStringWithOptions:0] forKey:@"icon"];
                        CFRelease(destination);
                        CFRelease(properties);
                        CFRelease(data);
                        [icon release];
                    }
                         
                }else{
                    IconRef iconRef = (IconRef)TISGetInputSourceProperty(s, kTISPropertyIconRef);
                    if(iconRef){
                        NSImage *icon = [[NSImage alloc]initWithIconRef:iconRef];
                        //return picture without memory leak; avoid the use of - TIFFRepresentation
                        NSRect imageRect = NSMakeRect(0, 0, icon.size.width , icon.size.height);
                        CGImageRef image = [icon CGImageForProposedRect:(NSRect *)&imageRect context:NULL hints:NULL];
                        CFMutableDataRef data = CFDataCreateMutable(kCFAllocatorDefault, 0);
                        CGImageDestinationRef destination = CGImageDestinationCreateWithData(data, kUTTypeTIFF, 1, NULL);
                        CFMutableDictionaryRef properties = CFDictionaryCreateMutable(kCFAllocatorDefault, 0, NULL, NULL);
                        CGImageDestinationAddImage(destination, image, properties);
                        CGImageDestinationFinalize(destination);
                        [dict setObject:[(NSData *)data base64EncodedStringWithOptions:0] forKey:@"icon"];
                        CFRelease(destination);
                        CFRelease(properties);
                        CFRelease(data);
                        [icon release];
                    }
                }

                [list addObject:dict];
                [dict release];
            }
        }
        CFRelease(sources);
    }
}

void INPUT_SOURCE_LIST(PA_PluginParameters params) {

    PA_CollectionRef ss = PA_CreateCollection();
    
    NSMutableArray *list = [[NSMutableArray alloc]init];
    
    PA_RunInMainProcess((PA_RunInMainProcessProcPtr)_input_sources_list, list);
    
    for(CFIndex i = 0; i < [list count]; ++i) {
        
        PA_ObjectRef o = PA_CreateObject();
        
        NSDictionary *dict = [list objectAtIndex:i];
        NSString *category = [dict objectForKey:@"category"];
        if(category != nil) ob_set_s(o, "category", [category UTF8String]);
        
        NSString *name = [dict objectForKey:@"name"];
        if(name != nil) ob_set_s(o, "name", [name UTF8String]);
        
        NSString *type = [dict objectForKey:@"type"];
        if(type != nil) ob_set_s(o, "type", [type UTF8String]);
        
        NSString *inputSourceID = [dict objectForKey:@"inputSourceID"];
        if(inputSourceID != nil) ob_set_s(o, "inputSourceID", [inputSourceID UTF8String]);
        
        NSString *bundleID = [dict objectForKey:@"bundleID"];
        if(bundleID != nil) ob_set_s(o, "bundleID", [bundleID UTF8String]);
        
        NSString *inputModeID = [dict objectForKey:@"inputModeID"];
        if(inputModeID != nil) ob_set_s(o, "inputModeID", [inputModeID UTF8String]);

        NSString *icon = [dict objectForKey:@"icon"];
        if(icon != nil) {
            NSData *data = [[NSData alloc]initWithBase64Encoding:icon];
            PA_Picture p = PA_CreatePicture((void *)[data bytes], (PA_long32)[data length]);
            ob_set_p(o, L"icon", p);
            [data release];
        }
        
        PA_Variable v = PA_CreateVariable(eVK_Object);
        PA_SetObjectVariable(&v, o);
        PA_SetCollectionElement(ss, PA_GetCollectionLength(ss), v);
        PA_ClearVariable(&v);
    }
    
    [list release];
    
    PA_ReturnCollection(params, ss);
}
