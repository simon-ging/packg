
_packg() {
    local cur prev opts
    _init_completion || return
    # complete first argument with script
    if [ $COMP_CWORD -eq 1 ]; then
        opts="caching constclass debugging dtime iotools.compressed iotools.file_indexer iotools.file_reader iotools.git_root_finder iotools.git_status_checker iotools.jsonext iotools.jsonext_encoder iotools.misc iotools.numpyext iotools.pathspec_matcher iotools.tomlext iotools.yamlext log magic misc multiproc.multiproc_fn multiproc.multiproc_producer_consumer packaging paths run.cleanup run.create_autocomplete run.show_env stats strings strings.abbreviations strings.base64utils strings.create_strings strings.hasher strings.quote_urlparse system.systemcall testing.fixture_webserver testing.import_from_source testing.setup_tests tqdmu typext web"
        COMPREPLY=( $( compgen -W "${opts}" -- "${cur}") )
        return 0
    fi
    # otherwise complete with filesystem
    COMPREPLY=( $(compgen -f -- "${cur}") )
    return 0
}

complete -F _packg packg
