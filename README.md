pymplb (PYthonMPLayerBindings) is a library that can be used to play media using an external MPlayer process.
To use pymplb you must have Python 2.6 or newer (Python3 should also work) and MPlayer installed.
The library runs the MPlayer binary in slave mode as a subprocess and then sends slave-mode commands to the process.
Commands are mapped to class methods and properties to class properties (by default prefixed with 'p\_').
Commands are discovered at runtime and thus these bindings should automatically also support any new commands added to MPlayer in the future.
An example:

```
>>> import pymplb
>>> player = pymplb.MPlayer()
>>> player.loadfile('test.ogv')
>>> player.p_filename
'test.ogv'
```

All available commands and properties can be used in this way. To see a complete list you can use the python interactive help. All methods take an additional keyword argument 'pausing'. This can be one of '', 'pausing', 'pausing\_keep', 'pausing\_toggle', and 'pausing\_keep\_force'. These affect how playback is affected by the command.

```
>>> player.get_property('filename', pausing='pausing')
'test.ogv'
```

See the MPlayer [slave-mode documentation](http://www.mplayerhq.hu/DOCS/tech/slave.txt) for details on pausing.

By default pymplb assumes that the binary "mplayer" is in your path. If this is not the case, or you want to use a differently named binary, you can do

```
>>> MPlayer2 = pymplb.make_mplayer_class(mplayer_bin='/usr/bin/mplayer')
>>> player = MPlayer2()
```

This is especially important when using the Windows OS since most programs are NOT in the path.

The reason why a new class is constructed instead of simply giving the binary path when constructing an MPlayer instance is that introspection capabilities would suffer: it would not be possible to see help for the class until an instance has been constructed. Anyway, this is a minor issue and in general you do not need to worry about this.

To prevent naming collisions between properties and methods the prefix 'p\_' is by default prepended to all property names. It is, however, not impossible that future version of MPlayer could have a property called 'foo' and a command called 'p\_foo', which would result in a naming conflict in pymplb. Therefore, it is also possible to change the prefix:

```
>>> MPlayer3 = pymplb.make_mplayer_class(method_prefix='m_', property_prefix='prop_')
>>> player = MPlayer3()
>>> player.m_loadfile('test.ogv')
>>> player.prop_filename
'test.ogv'
```

Support the developer if you like this project:

[![Donate using Liberapay](https://liberapay.com/assets/widgets/donate.svg)](https://liberapay.com/saparvia/donate)
