#!/usr/bin/env python2

# TODO: this can't be the real location!
# Install at /usr/libexec/kubernetes/kubelet-plugins/volume/exec/smc~smc-storage/smc-storage

import json, os, shutil, sys

def LOG(*args):
    open("/tmp/a",'a').write(str(args)+'\n')

LOG('argsv', sys.argv)

def log(obj):
    print(json.dumps(obj))

def cmd(s):
    z = os.popen(s)
    t = z.read()
    if z.close():
        raise RuntimeError(t)

def init(args):
    LOG('init', args)
    # TODO: would ensure zfs kernel module is available (?)
    return

def image_filename(project_id):
    return os.path.join("/tmp/%s.img"%project_id)

# Attach device to minion
def attach(args):
    LOG('attach', args)
    params = json.loads(args.json_params)
    project_id = params.get("project_id", None)
    if not project_id:
        raise RuntimeError("must specify project_id")
    img = image_filename(project_id)
    if not os.path.exists(img):
        cmd('truncate -s 3G %s'%img)
        format = True
    else:
        format = False
    device = os.popen("losetup -v -f %s"%img).read().split()[-1]
    if format:
        cmd('mkfs.ext4 -q %s'%device)
    return {'device':device}


def mount(args):
    LOG('mount', args)
    mount_dir  = args.mount_dir
    device     = args.device
    params     = json.loads(args.json_params)
    if not os.path.exists(mount_dir):
        os.makedirs(mount_dir)
    cmd("mount %s %s"%(device, mount_dir))

def unmount(args):
    LOG('unmount', args)
    mount_dir  = args.mount_dir
    if os.path.exists(mount_dir):
        cmd("umount %s"%mount_dir)

def detach(args):
    LOG('detach', args)
    device = args.device
    cmd("losetup -d %s"%device)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='SMC Storage k8s vendor driver')
    subparsers = parser.add_subparsers(help='sub-command help')

    sub = subparsers.add_parser('init', help='initialize the storage driver')
    sub.set_defaults(func=init)

    sub = subparsers.add_parser('attach', help='attach to NFS server and create or import the remote ZFS pool')
    sub.add_argument('json_params', type=str, help="""json of object '{"project_id": "f8cf98ed-299e-4423-a167-870e8658e081"}""")
    sub.set_defaults(func=attach)

    sub = subparsers.add_parser('mount', help='mount the ZFS pool, which is assumed to exist, at a given mountpoint; also create bind mounts for snapshots')
    sub.add_argument('mount_dir', type=str, help='mount dir')
    sub.add_argument('device', type=str, help='device name')
    sub.add_argument('json_params', type=str, help='json params {...}')
    sub.set_defaults(func=mount)

    sub = subparsers.add_parser('unmount', help='')
    sub.add_argument('mount_dir', type=str, help='mount dir')
    sub.set_defaults(func=unmount)

    sub = subparsers.add_parser('detach', help='export ZFS pool and remove snapshot bind mount')
    sub.add_argument('device', type=str, help='mount device')
    sub.set_defaults(func=detach)

    args = parser.parse_args()
    if hasattr(args, 'func'):
        try:
            x = args.func(args)
            obj = {"status": "Success"}
            if x:
                obj.update(x)
            log(obj)
            sys.exit(0)
        except Exception as msg:
            log({'status':'Failure', 'message':repr(msg)})
            sys.exit(1)