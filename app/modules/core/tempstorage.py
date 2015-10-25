temp_folder_prefix = None

def get_temp_folder_prefix():
    global temp_folder_prefix
    if temp_folder_prefix:
        return temp_folder_prefix
    from kivy import platform
    if platform == 'android':
        from jnius import autoclass, cast
        PythonActivity = autoclass('org.renpy.android.PythonActivity')
        context = cast('android.content.Context', PythonActivity.mActivity)
        tempfolder = str(context.getExternalFilesDir(None).getAbsolutePath())
    elif platform == 'ios':
        from os.path import expanduser
        tempfolder = expanduser('~/Documents/')
    else:
        import tempfile
        tempfolder = tempfile.gettempdir()

    from os.path import join
    temp_folder_prefix = join(tempfolder, 'insiderr_')
    return temp_folder_prefix
